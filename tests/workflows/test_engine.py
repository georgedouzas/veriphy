"""Test workflows as data: the next step from the target's records in time order, and running up to an agent."""

from pathlib import Path

import pytest

from veriphy.core import StepError, check_config, resolve
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


def _results(lines: list[str]) -> list[str]:
    """Return the step and status of each step a run reports, and how the run ends, as `step: status`."""
    said = [line for line in lines if not line.startswith(' ')]
    return [f"{line.split(' ', 1)[0]}: {line.rsplit(': ', 1)[-1]}" for line in said[:-1]] + [said[-1]]


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
    assert run_workflow(workspace, 'flow', 'Claim.lean', {})[-1] == 'flow on Claim.lean: stopped: counterexample'


def test_back_to_an_earlier_entry_until_a_newer_record(workspace: Path) -> None:
    """Return to the agent after a refusal, and go on once it records a newer artifact."""
    _write(workspace, 'broken')
    lines = run_workflow(workspace, 'flow', 'Claim.lean', {})
    waiting = '  veriphy layers step write Claim.lean --by <your name>'
    assert _results(lines)[:2] == ['test: refused', 'verify: refused']
    assert waiting in lines
    assert next_step(workspace, 'flow', 'Claim.lean').step == 'write'
    _write(workspace, 'fixed')
    assert run_workflow(workspace, 'flow', 'Claim.lean', {})[-1] == 'flow on Claim.lean: done'


def test_attempts_exhausted_and_a_condition(workspace: Path) -> None:
    """Move to `exhausted` once the attempts are used, where the condition holds since nothing granted `kernel`."""
    _write(workspace, 'broken')
    run_workflow(workspace, 'flow', 'Claim.lean', {})
    _write(workspace, 'still broken')
    lines = run_workflow(workspace, 'flow', 'Claim.lean', {})
    assert _results(lines)[-2:] == ['sample: refused', 'flow on Claim.lean: done']


def test_a_proof_skips_the_condition(workspace: Path) -> None:
    """Skip an entry whose condition fails: once a record grants a `kernel` level, `sample` does not run."""
    _write(workspace, 'fine')
    lines = run_workflow(workspace, 'flow', 'Claim.lean', {})
    assert _results(lines) == ['test: accepted', 'verify: accepted', 'flow on Claim.lean: done']


def test_same_records_same_answer(workspace: Path) -> None:
    """Give the same answer twice for the same records."""
    _write(workspace, 'broken')
    run_workflow(workspace, 'flow', 'Claim.lean', {})
    assert next_step(workspace, 'flow', 'Claim.lean') == next_step(workspace, 'flow', 'Claim.lean')


def test_shipped_workflows_name_real_steps(tmp_path: Path) -> None:
    """Pass the check for the shipped workflows, with the math and social-science packs each."""
    for packs in ('[math]', '[social-science]'):
        (tmp_path / 'veriphy.yaml').write_text(f'version: 1\npacks: {packs}\n')
        assert check_config(resolve(tmp_path)) == []


def test_run_refuses_a_target_its_records_do_not_name(workspace: Path) -> None:
    """Stop and name the step's first input when a step it ran wrote a record that does not name the target."""
    (workspace / 'Claim.lean').write_text('fine')
    (workspace / 'Other.lean').write_text('fine')
    run_step(load_steps(workspace)['write'], workspace, {'artifact': 'Other.lean', 'by': 'agent'})
    with pytest.raises(StepError, match="the target must be each step's first input, here its file"):
        run_workflow(workspace, 'flow', 'Other.lean', {'file': 'Claim.lean'})
