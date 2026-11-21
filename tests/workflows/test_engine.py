"""Test workflows as data: the next step from the target's records in time order, and running up to an agent."""

from pathlib import Path

import pytest

from veriphy.core import check_config, resolve
from veriphy.steps import load_steps, run_step
from veriphy.workflows import next_step, run_workflow

FUNCTIONS = """
from pathlib import Path


def judge(inputs):
    text = Path(inputs['file']).read_text()
    status = 'counterexample' if 'false' in text else 'refused' if 'broken' in text else 'accepted'
    return {'status': status}
"""
PACK = """version: 1
name: flow
requires: [core]
levels:
  proved: {trust: kernel, above: none}
primitives:
  flow.judge:
    function: flow_functions:judge
    trust: kernel
    input: {type: object, required: [file]}
    output: {type: object, required: [status]}
steps:
  write:
    kind: agent
    inputs: {artifact: {scope: file, path: true}}
  test:
    kind: evidence
    primitive: flow.judge
    inputs: {file: {scope: file, path: true}}
  verify:
    kind: check
    primitive: flow.judge
    grants: proved
    inputs: {file: {scope: file, path: true}}
  sample:
    kind: evidence
    primitive: flow.judge
    inputs: {file: {scope: file, path: true}}
workflows:
  flow:
    - write
    - test: {counterexample: stop}
    - verify: {refused: write, attempts: 2, exhausted: sample}
    - sample: {when: {without: kernel}}
"""


@pytest.fixture
def workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Return a workspace of the `flow` pack, whose verdict follows the target file's words."""
    (tmp_path / 'lakefile.toml').write_text('')
    (tmp_path / 'veriphy.yaml').write_text('version: 1\npacks: [./flow]\n')
    (tmp_path / 'flow').mkdir()
    (tmp_path / 'flow' / 'pack.yaml').write_text(PACK)
    (tmp_path / 'flow_functions.py').write_text(FUNCTIONS)
    monkeypatch.syspath_prepend(str(tmp_path))
    return tmp_path


def _write(root: Path, text: str) -> None:
    """Have the agent write the claim, and record it."""
    (root / 'Claim.lean').write_text(text)
    run_step(load_steps(root)['write'], root, {'artifact': 'Claim.lean', 'by': 'agent'})


def test_undefined_steps_and_entries_are_refused(workspace: Path) -> None:
    """Refuse a workflow naming a step no pack defines, or going to an entry it does not have."""
    broken = PACK.replace("    - write\n", "    - certfy\n    - write: {written: nowhere}\n")
    (workspace / 'flow' / 'pack.yaml').write_text(broken)
    problems = check_config(resolve(workspace))
    assert any("workflows.flow names the step 'certfy'" in p for p in problems)
    assert any("write goes to 'nowhere'" in p for p in problems)


def test_the_agent_starts(workspace: Path) -> None:
    """Name the agent step first, before any record."""
    planned = next_step(workspace, 'flow', 'Claim.lean')
    assert (planned.step, planned.agent) == ('write', True)


def test_a_counterexample_stops(workspace: Path) -> None:
    """Stop on a counterexample, naming the status."""
    _write(workspace, 'false')
    assert run_workflow(workspace, 'flow', 'Claim.lean', {})[-1] == 'flow: counterexample'


def test_back_to_an_earlier_entry_until_a_newer_record(workspace: Path) -> None:
    """Return to the agent after a refusal, and go on once it records a newer artifact."""
    _write(workspace, 'broken')
    lines = run_workflow(workspace, 'flow', 'Claim.lean', {})
    waiting = 'flow: waiting for write: record the artifact, as veriphy write Claim.lean'
    assert lines == ['test: refused', 'verify: refused', waiting]
    assert next_step(workspace, 'flow', 'Claim.lean').step == 'write'
    _write(workspace, 'fixed')
    assert run_workflow(workspace, 'flow', 'Claim.lean', {})[-1] == 'flow: done'


def test_attempts_exhausted_and_a_condition(workspace: Path) -> None:
    """Move to `exhausted` once the attempts are used, where the condition holds since nothing granted `kernel`."""
    _write(workspace, 'broken')
    run_workflow(workspace, 'flow', 'Claim.lean', {})
    _write(workspace, 'still broken')
    lines = run_workflow(workspace, 'flow', 'Claim.lean', {})
    assert lines[-2:] == ['sample: refused', 'flow: done']


def test_a_proof_skips_the_condition(workspace: Path) -> None:
    """Skip an entry whose condition fails: once a record grants a `kernel` level, `sample` does not run."""
    _write(workspace, 'fine')
    assert run_workflow(workspace, 'flow', 'Claim.lean', {}) == ['test: accepted', 'verify: accepted', 'flow: done']


def test_same_records_same_answer(workspace: Path) -> None:
    """Give the same answer twice for the same records."""
    _write(workspace, 'broken')
    run_workflow(workspace, 'flow', 'Claim.lean', {})
    assert next_step(workspace, 'flow', 'Claim.lean') == next_step(workspace, 'flow', 'Claim.lean')


def test_shipped_workflows_name_real_steps(tmp_path: Path) -> None:
    """Pass the check for the shipped workflows, with the math and reproduction packs each."""
    for packs in ('[math]', '[reproduction]'):
        (tmp_path / 'veriphy.yaml').write_text(f'version: 1\npacks: {packs}\n')
        assert check_config(resolve(tmp_path)) == []
