"""Test declared steps: a primitive with inputs, their digest scopes, comparison, agent steps and the command."""

from pathlib import Path

import pytest
from click.testing import CliRunner

from veriphy.__main__ import veriphy
from veriphy.core import check_config, resolve
from veriphy.packs.lean.steps import lean_imports
from veriphy.steps import RecordStore, load_steps, run_step

FUNCTIONS = """
def estimate(inputs):
    return {'status': 'reported', 'estimate': inputs['x'] * 2}
"""
PACK = """version: 1
name: econ
requires: [core]
primitives:
  econ.estimate:
    function: econ_functions:estimate
    trust: reproduction
    input: {type: object, required: [x], properties: {x: {type: number}}}
    output: {type: object, required: [estimate]}
steps:
  estimate:
    kind: evidence
    primitive: econ.estimate
    help: twice the value
    inputs:
      x: {type: integer, help: the value}
  reproduce:
    kind: check
    primitive: econ.estimate
    grants: reproduced
    compare: {field: estimate, against: claimed, tolerance: 0.5}
    inputs:
      x: {type: integer}
      claimed: {type: integer, record: true}
  broken:
    kind: evidence
    primitive: econ.nosuch
    inputs:
      x: {scope: nosuch}
"""


@pytest.fixture
def workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Return a workspace of `core` and a local pack whose steps are YAML over a Python function primitive."""
    (tmp_path / 'lakefile.toml').write_text('')
    (tmp_path / 'veriphy.yaml').write_text('version: 1\npacks: [./econ]\n')
    (tmp_path / 'econ').mkdir()
    (tmp_path / 'econ' / 'pack.yaml').write_text(PACK)
    (tmp_path / 'econ_functions.py').write_text(FUNCTIONS)
    monkeypatch.syspath_prepend(str(tmp_path))
    return tmp_path


def test_a_step_from_yaml_alone(workspace: Path) -> None:
    """Run a step a pack declares in YAML, over a primitive, and record it."""
    result = run_step(load_steps(workspace)['estimate'], workspace, {'x': 21})
    assert (result.record.status, result.record.outputs['estimate']) == ('reported', 42)
    assert RecordStore(workspace).all('estimate') == [result.path]


def test_unknown_primitive_and_scope_are_refused(workspace: Path) -> None:
    """Name the step and what it names when its primitive or scope is not declared."""
    problems = check_config(resolve(workspace))
    assert "steps.broken names the primitive 'econ.nosuch'" in problems[0]
    assert "steps.broken.inputs.x names the scope 'nosuch'" in problems[1]


def test_compare_within_and_beyond_the_tolerance(workspace: Path) -> None:
    """Grant the level when the estimate agrees with the claim, and record both values either way."""
    step = load_steps(workspace)['reproduce']
    agrees = run_step(step, workspace, {'x': 5, 'claimed': 10}).record
    assert (agrees.status, agrees.level, agrees.outputs['compared']) == (
        'agrees',
        'reproduced',
        {'field': 'estimate', 'found': 10.0, 'claimed': 10.0, 'tolerance': 0.5},
    )
    differs = run_step(step, workspace, {'x': 5, 'claimed': 12}).record
    assert (differs.status, differs.level, differs.outputs['claimed']) == ('differs', None, 12)


def test_agent_step_records_the_artifact(workspace: Path) -> None:
    """Record an agent's artifact by digest with its author, and a new record when the artifact changes."""
    claim = workspace / 'Claim.lean'
    claim.write_text('theorem t : 1 = 1 := rfl\n')
    step = load_steps(workspace)['formalize']
    first = run_step(step, workspace, {'artifact': 'Claim.lean', 'by': 'agent'}).record
    assert (first.kind, first.status, first.outputs['author']) == ('agent', 'written', 'agent')
    claim.write_text('theorem t : 2 = 2 := rfl\n')
    assert run_step(step, workspace, {'artifact': 'Claim.lean', 'by': 'agent'}).record.digest != first.digest


def test_lean_imports_follows_imports(tmp_path: Path) -> None:
    """Keep a Lean file's digest through an edit to a file it does not import, and change it otherwise."""
    (tmp_path / 'lean-toolchain').write_text('leanprover/lean4:v4.34.1\n')
    (tmp_path / 'Pkg').mkdir()
    (tmp_path / 'Pkg' / 'Base.lean').write_text('def b := 1\n')
    (tmp_path / 'Pkg' / 'Other.lean').write_text('def o := 1\n')
    claim = tmp_path / 'Claim.lean'
    claim.write_text('import Mathlib\nimport Pkg.Base\n\ntheorem t : Pkg.b = 1 := rfl\n')
    before = lean_imports(tmp_path, claim)
    (tmp_path / 'Pkg' / 'Other.lean').write_text('def o := 2\n')
    assert lean_imports(tmp_path, claim) == before
    (tmp_path / 'Pkg' / 'Base.lean').write_text('def b := 2\n')
    assert lean_imports(tmp_path, claim) != before
    edited = lean_imports(tmp_path, claim)
    (tmp_path / 'lean-toolchain').write_text('leanprover/lean4:v4.35.0\n')
    assert lean_imports(tmp_path, claim) != edited


def test_the_command_follows_the_declaration(workspace: Path) -> None:
    """Make required inputs arguments and the others options, and list each step with its pack."""
    runner = CliRunner()
    shown = runner.invoke(veriphy, ['--root', str(workspace), 'reproduce', '--help'])
    assert 'Usage: veriphy reproduce [OPTIONS] X CLAIMED' in shown.output
    listed = runner.invoke(veriphy, ['--root', str(workspace), 'steps'])
    assert 'estimate\tevidence\tecon\ttwice the value' in listed.output
    assert 'formalize\tagent\tcore' in listed.output
    ran = runner.invoke(veriphy, ['--root', str(workspace), 'estimate', '4'])
    assert (ran.exit_code, 'estimate: reported' in ran.output) == (0, True)
