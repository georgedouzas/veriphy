"""Test the Lean primitives: one REPL environment per import header, with the same output as `lake env lean`."""

import shutil
from pathlib import Path

import pytest

from veriphy.packs.lean.primitives import _methods as methods
from veriphy.packs.lean.primitives._runner import Runner

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


def _without_tools(output: dict[str, object]) -> dict[str, object]:
    """Return an output without the tools that produced it, which differ between the REPL and a file run."""
    return {key: value for key, value in output.items() if key != 'tools'}


def test_one_environment_for_one_header(monkeypatch: pytest.MonkeyPatch) -> None:
    """Load the imports once for two files with the same header, and give the output a file run gives."""
    kept = Runner()
    monkeypatch.setattr(methods, 'runner', lambda: kept)
    try:
        repl = kept.repl(ROOT)
        if repl is None:
            pytest.skip('no Lean REPL could be set up here')
        results = [methods.check({'root': str(ROOT), 'source': s}) for s in (FIRST, SECOND, BROKEN)]
        assert len(repl.environments) == 1
    finally:
        kept.close()
    monkeypatch.setenv('VERIPHY_LEAN_REPL', 'off')
    files = Runner()
    monkeypatch.setattr(methods, 'runner', lambda: files)
    expected = [methods.check({'root': str(ROOT), 'source': s}) for s in (FIRST, SECOND, BROKEN)]
    assert [r['status'] for r in results] == ['accepted', 'accepted', 'refused']
    assert [_without_tools(r) for r in results] == [_without_tools(e) for e in expected]


def test_serialize_a_claim(monkeypatch: pytest.MonkeyPatch) -> None:
    """Serialize a claim with its kind, its statement, and the names its proof introduces."""
    monkeypatch.setenv('VERIPHY_LEAN_REPL', 'off')
    files = Runner()
    monkeypatch.setattr(methods, 'runner', lambda: files)
    result = methods.serialize({'root': str(ROOT), 'source': CLAIM, 'declaration': 't'})
    assert (result['status'], result['kind'], result['declaration']) == ('serialized', 'theorem', 't')
    problem = result['problem']
    assert isinstance(problem, dict)
    assert problem['intros'] == ['x', 'h']
    assert problem['universal'] == [{'name': 'x', 'type': 'ℝ'}]
