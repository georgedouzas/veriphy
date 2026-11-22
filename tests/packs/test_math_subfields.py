"""Test the subfields of mathematics, nested in the math pack: number theory (PARI), group theory (GAP), graph theory.

Each runs its own function under Sage, through the math pack's `sage` tool, and grants `oracle-test` to a correct
claim and nothing to a wrong one.
"""

import shutil
from pathlib import Path

import pytest

from veriphy.core import check_config, resolve
from veriphy.steps import load_steps, run_step

ROOT = Path(__file__).resolve().parents[2]
pytestmark = pytest.mark.skipif(shutil.which('sage') is None, reason='needs SageMath')


@pytest.fixture(autouse=True)
def _this_trees_sage(monkeypatch: pytest.MonkeyPatch) -> None:
    """Run the Sage tool from this tree, which holds the subfields' functions."""
    monkeypatch.setenv(
        'VERIPHY_SAGE_SESSION',
        str(ROOT / 'src' / 'veriphy' / 'packs' / 'math' / 'primitives' / 'sage' / '__main__.py'),
    )
    monkeypatch.setenv('PYTHONPATH', str(ROOT / 'src'))


def _workspace(root: Path, pack: str) -> Path:
    """Write a workspace of one subfield of mathematics."""
    (root / 'veriphy.yaml').write_text(f'version: 1\npacks: [{pack}]\n')
    resolved = resolve(root)
    assert check_config(resolved) == []
    assert [p.name for p in resolved.packs] == ['core', 'math', pack]
    return root


def _run(root: Path, step: str, **inputs: object) -> tuple[str, str | None, dict[str, object]]:
    """Run a step and return its status, level and outputs."""
    record = run_step(load_steps(root)[step], root, inputs).record
    return record.status, record.level, record.outputs


def test_factorizations_are_checked_with_pari(tmp_path: Path) -> None:
    """Accept the factorization of 2^67 - 1, and refuse the claim that it is prime."""
    root = _workspace(tmp_path, 'number-theory')
    number = str(2**67 - 1)
    assert _run(root, 'check-factorization', number=number, claimed='193707721 * 761838257287')[:2] == (
        'accepted',
        'oracle-test',
    )
    status, level, outputs = _run(root, 'check-factorization', number=number, claimed=number)
    assert (status, level, outputs['factorization']) == ('refused', None, '193707721 * 761838257287')


def test_class_numbers_are_certified(tmp_path: Path) -> None:
    """Accept h(Q(√-5)) = 2, and refuse h(Q(√-23)) = 1, whose class number is 3."""
    root = _workspace(tmp_path, 'number-theory')
    assert _run(root, 'check-class-number', polynomial='x^2 + 5', claimed='2')[:2] == ('accepted', 'oracle-test')
    status, _, outputs = _run(root, 'check-class-number', polynomial='x^2 + 23', claimed='1')
    assert (status, outputs['class_number']) == ('refused', 3)


def test_groups_are_checked_with_gap(tmp_path: Path) -> None:
    """Accept SmallGroup(12, 3) as A4, refuse D8 as abelian, and evaluate nothing but a group constructor."""
    root = _workspace(tmp_path, 'group-theory')
    assert _run(root, 'check-group', group='SmallGroup(12, 3)', property='structure', claimed='A4')[:2] == (
        'accepted',
        'oracle-test',
    )
    assert _run(root, 'check-group', group='DihedralGroup(8)', property='abelian', claimed='true')[0] == 'refused'
    assert _run(root, 'check-group', group='Exec("ls")', property='order', claimed='1')[0] == 'failed'


def test_graphs_are_checked_with_sage(tmp_path: Path) -> None:
    """Accept the Petersen graph's chromatic number and girth, and refuse that it is Hamiltonian."""
    root = _workspace(tmp_path, 'graph-theory')
    petersen = 'PetersenGraph()'
    assert _run(root, 'check-graph', graph=petersen, property='chromatic-number', claimed='3')[:2] == (
        'accepted',
        'oracle-test',
    )
    assert _run(root, 'check-graph', graph=petersen, property='girth', claimed='5')[0] == 'accepted'
    assert _run(root, 'check-graph', graph=petersen, property='hamiltonian', claimed='true')[:2] == ('refused', None)
