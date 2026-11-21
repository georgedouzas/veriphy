"""Test the step runner: replay of final records, reruns that keep a changed result, and the kind rule."""

from pathlib import Path

import pytest

from veriphy.core import StepError
from veriphy.steps import Outcome, Params, Prepared, RecordStore, Step, exit_code, run_step


def _counting_step(statuses: list[str], kind: str = 'check', level: str | None = None) -> tuple[Step, list[int]]:
    """Return a step that answers the given statuses in turn, and the list its runs are counted in."""
    calls: list[int] = []

    def prepare(_root: Path, params: Params) -> Prepared:
        path = Path(str(params['file']))
        return Prepared({'file': path.read_text()}, {'file': str(path)})

    def execute(_root: Path, _params: Params, _prepared: Prepared) -> Outcome:
        calls.append(1)
        return Outcome(statuses[min(len(calls), len(statuses)) - 1], level=level)

    return Step('probe', kind, prepare, execute), calls


@pytest.fixture
def source(tmp_path: Path) -> Path:
    """Return an input file."""
    path = tmp_path / 'input.txt'
    path.write_text('claim')
    return path


def test_replay_runs_nothing(tmp_path: Path, source: Path) -> None:
    """Return the stored record for the same inputs without running the step."""
    step, calls = _counting_step(['accepted'])
    first = run_step(step, tmp_path, {'file': str(source)})
    second = run_step(step, tmp_path, {'file': str(source)})
    assert (len(calls), first.replayed, second.replayed) == (1, False, True)
    assert second.record == first.record


def test_moved_input_replays(tmp_path: Path, source: Path) -> None:
    """Keep the digest and the record when an input moves with the same content."""
    step, calls = _counting_step(['accepted'])
    first = run_step(step, tmp_path, {'file': str(source)})
    moved = source.rename(tmp_path / 'moved.txt')
    second = run_step(step, tmp_path, {'file': str(moved)})
    assert second.replayed
    assert second.record.digest == first.record.digest
    assert len(calls) == 1


def test_rerun_keeps_a_changed_result(tmp_path: Path, source: Path) -> None:
    """Write nothing when a rerun agrees, and keep both records when it differs."""
    step, _ = _counting_step(['accepted', 'accepted', 'refused'])
    first = run_step(step, tmp_path, {'file': str(source)})
    same = run_step(step, tmp_path, {'file': str(source)}, rerun=True)
    changed = run_step(step, tmp_path, {'file': str(source)}, rerun=True)
    assert (same.changed, same.path) == (False, first.path)
    assert changed.changed
    assert len(RecordStore(tmp_path).variants('probe', first.record.digest)) == 2


def test_unchecked_record_runs_again(tmp_path: Path, source: Path) -> None:
    """Run again after an unchecked result, instead of replaying it."""
    step, calls = _counting_step(['unchecked', 'entailed'])
    run_step(step, tmp_path, {'file': str(source)})
    second = run_step(step, tmp_path, {'file': str(source)})
    assert (len(calls), second.replayed, second.record.status) == (2, False, 'entailed')


def test_evidence_step_cannot_grant_a_level(tmp_path: Path, source: Path) -> None:
    """Refuse an evidence step that returns a level, and record nothing."""
    step, _ = _counting_step(['accepted'], kind='evidence', level='certificate')
    with pytest.raises(StepError, match='grants no level'):
        run_step(step, tmp_path, {'file': str(source)})
    assert not RecordStore(tmp_path).all()


@pytest.mark.parametrize(
    ('status', 'code'),
    [
        ('entailed', 0),
        ('conforms', 0),
        ('written', 0),
        ('refused', 1),
        ('violations', 1),
        ('failed', 1),
        ('unchecked', 3),
        ('incomplete', 3),
    ],
)
def test_exit_codes(status: str, code: int) -> None:
    """Map each status to the command's exit status."""
    assert exit_code(status) == code
