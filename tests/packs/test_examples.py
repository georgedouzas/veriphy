"""Test the example packs the guide documents: `economics` (a Python function) and `history` (a command), combined."""

import shutil
from pathlib import Path

import pytest

from veriphy.core import check_config, level_order, resolve
from veriphy.steps import load_steps, run_step

EXAMPLES = Path(__file__).resolve().parents[2] / 'docs' / 'examples' / 'packs'
# both packs place a level directly above `none`, so the workspace says which is lower, as the guide shows
WORKSPACE = """version: 1
packs: [./packs/economics, ./packs/history]
levels:
  quoted: {above: recomputed}
"""


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    """Return a workspace of both example packs, a table and a source text."""
    shutil.copytree(EXAMPLES, tmp_path / 'packs')
    (tmp_path / 'veriphy.yaml').write_text(WORKSPACE)
    (tmp_path / 'table.csv').write_text('country,growth\nA,2.0\nB,3.0\nC,4.1\n')
    (tmp_path / 'novel.txt').write_text('It was the best of times,\nit was the worst of times.\n')
    return tmp_path


def test_the_packs_combine(workspace: Path) -> None:
    """Pass the check once the workspace orders the two packs' levels, and list both packs' steps."""
    resolved = resolve(workspace)
    assert check_config(resolved) == []
    assert level_order(resolved) == ('none', 'recomputed', 'quoted')
    assert {'recompute', 'verify-quote', 'record-claims'} <= set(load_steps(workspace))


def test_a_level_conflict_is_named(workspace: Path) -> None:
    """Name the two levels that both sit directly above `none` when the workspace doesn't order them."""
    (workspace / 'veriphy.yaml').write_text('version: 1\npacks: [./packs/economics, ./packs/history]\n')
    assert any('quoted and recomputed are both directly above' in p for p in check_config(resolve(workspace)))


def test_recompute_agrees_or_differs(workspace: Path) -> None:
    """Grant `recomputed` when the mean agrees with the claim, and nothing when it differs."""
    step = load_steps(workspace)['recompute']
    agrees = run_step(step, workspace, {'data': 'table.csv', 'column': 'growth', 'claimed': 3.03}).record
    assert (agrees.status, agrees.level) == ('agrees', 'recomputed')
    differs = run_step(step, workspace, {'data': 'table.csv', 'column': 'growth', 'claimed': 3.5}).record
    assert (differs.status, differs.level) == ('differs', None)
    unclaimed = run_step(step, workspace, {'data': 'table.csv', 'column': 'growth'}).record
    assert (unclaimed.status, unclaimed.level) == ('reported', None)


def test_verify_quote_accepts_only_found(workspace: Path) -> None:
    """Grant `quoted` for a passage found across a line break, and refuse a missing one, keeping the tool's word."""
    step = load_steps(workspace)['verify-quote']
    found = run_step(step, workspace, {'source': 'novel.txt', 'passage': 'best of times, it was the worst'}).record
    assert (found.status, found.level, found.outputs['line']) == ('found', 'quoted', 1)
    missing = run_step(step, workspace, {'source': 'novel.txt', 'passage': 'age of wisdom'}).record
    assert (missing.status, missing.level, missing.outputs['result']) == ('refused', None, 'missing')


def test_a_granting_step_must_say_what_accepts(workspace: Path) -> None:
    """Refuse a step that grants a level over a tool with statuses of its own, when it names no `accepts`."""
    pack = workspace / 'packs' / 'history' / 'pack.yaml'
    pack.write_text(pack.read_text().replace('    accepts: [found]\n', ''))
    assert any("say which statuses mean success with `accepts`" in p for p in check_config(resolve(workspace)))
