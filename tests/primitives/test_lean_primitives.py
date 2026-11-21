"""Test the Lean primitives: a check of each file, and a claim serialized, each in one `lake env lean` run."""

import shutil
from pathlib import Path

import pytest

from veriphy.packs.lean.primitives import _methods as methods

ROOT = Path(__file__).resolve().parents[2]
pytestmark = pytest.mark.skipif(
    shutil.which('lake') is None or not (ROOT / '.lake' / 'build').is_dir(),
    reason='needs a built Lean workspace (`lake build`)',
)
HEADER = 'import Mathlib.Analysis.SpecialFunctions.Pow.Real\n\n'
FIRST = HEADER + 'theorem one : (2 : ℝ) + 2 = 4 := by norm_num\n'
SECOND = HEADER + 'theorem two (x : ℝ) : 0 ≤ x ^ 2 := by positivity\n'
CLAIM = HEADER + 'theorem t (x : ℝ) (h : 0 ≤ x) : 0 ≤ x ^ 3 := by positivity\n'
BROKEN = HEADER + 'theorem bad : (2 : ℝ) + 2 = 5 := by norm_num\n'


def test_check_accepts_and_refuses() -> None:
    """Accept two true files and refuse a false one, naming the workspace's Lean as the tool."""
    results = [methods.check({'root': str(ROOT), 'source': s}) for s in (FIRST, SECOND, BROKEN)]
    assert [r['status'] for r in results] == ['accepted', 'accepted', 'refused']
    assert all([tool['name'] for tool in r['tools']] == ['lean'] for r in results)


def test_serialize_a_claim() -> None:
    """Serialize a claim with its kind, its statement, and the names its proof introduces."""
    result = methods.serialize({'root': str(ROOT), 'source': CLAIM, 'declaration': 't'})
    assert (result['status'], result['kind'], result['declaration']) == ('serialized', 'theorem', 't')
    problem = result['problem']
    assert isinstance(problem, dict)
    assert problem['intros'] == ['x', 'h']
    assert problem['universal'] == [{'name': 'x', 'type': 'ℝ'}]
