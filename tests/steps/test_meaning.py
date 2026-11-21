"""Test the `meaning` step on this repository's workspace: a seeded check of a statement, recorded as evidence."""

import shutil
from collections.abc import Iterator
from pathlib import Path

import pytest

from veriphy.__main__ import main
from veriphy.steps import RecordStore, config_digest, input_digest, load_steps, run_step

ROOT = Path(__file__).resolve().parents[2]
MEANING = load_steps(ROOT)['meaning']
pytestmark = pytest.mark.skipif(
    shutil.which('lake') is None or shutil.which('sage') is None or not (ROOT / '.lake' / 'build').is_dir(),
    reason='needs a built Lean workspace (`lake build`) and SageMath',
)
CLAIM = """import Mathlib.Analysis.SpecialFunctions.Pow.Real

def wrong : Prop := ∀ x : ℝ, 0 ≤ x → Real.sqrt (x ^ 2) = -x
"""


@pytest.fixture(autouse=True)
def _daemon_and_records(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Serve Lean's requests with this tree's daemon, and delete the records a test writes into the workspace."""
    monkeypatch.setenv('VERIPHY_SAGE_SERVER', str(ROOT / 'src' / 'veriphy' / 'sage_server' / '__main__.py'))
    monkeypatch.setenv('PYTHONPATH', str(ROOT / 'src'))
    before = set(RecordStore(ROOT).all())
    yield
    for path in set(RecordStore(ROOT).all()) - before:
        path.unlink()


def test_meaning_records_a_counterexample_as_evidence(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Record a counterexample with the agent's reading, as evidence with no level; replay it; exit with status 1."""
    path = tmp_path / 'Claim.lean'
    path.write_text(CLAIM)
    params = {'file': str(path), 'declaration': 'wrong', 'informal': 'the square root of x squared is minus x'}
    first = run_step(MEANING, ROOT, params, rerun=True)
    record = first.record
    assert (record.kind, record.status, record.level, record.seed) == ('evidence', 'counterexample', None, 0)
    assert record.outputs['informal'] == params['informal']
    assert record.outputs['counterexample'] == {
        'values': {'x': '1'},
        'statement': '√(x ^ 2) = -x',
        'lhs': '1',
        'rhs': '-1',
        'difference': '2',
    }
    assert 'sage' in record.tools
    again = run_step(MEANING, ROOT, params)
    assert again.replayed
    assert again.record == record
    with pytest.raises(SystemExit) as exit_info:
        main(['--root', str(ROOT), 'meaning', str(path), 'wrong', '--informal', str(params['informal'])])
    assert exit_info.value.code == 1
    assert 'meaning: counterexample (replayed)' in capsys.readouterr().out


def test_meaning_digest_covers_the_reading_and_the_seed(tmp_path: Path) -> None:
    """Give another digest when the agent's reading or the seed changes, without running anything."""
    path = tmp_path / 'Claim.lean'
    path.write_text(CLAIM)
    base: dict[str, object] = {'file': str(path), 'declaration': 'wrong', 'informal': 'one reading'}

    def digest(params: dict[str, object]) -> str:
        """Return the digest the step would record for the parameters."""
        prepared = MEANING.prepare(ROOT, params)
        return input_digest(MEANING.name, prepared.contents, config_digest(ROOT), prepared.seed)

    assert digest(base) == digest(dict(base))
    assert digest(base) != digest({**base, 'informal': 'another reading'})
    assert digest(base) != digest({**base, 'seed': 1})
