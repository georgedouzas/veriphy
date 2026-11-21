"""Test the Lean steps on this repository's workspace: `check` reports errors and axioms, `level` the levels."""

import shutil
from collections.abc import Iterator
from pathlib import Path

import pytest

from veriphy.__main__ import main
from veriphy.packs.lean.steps import CHECK, LEVEL
from veriphy.steps import RecordStore, run_step

ROOT = Path(__file__).resolve().parents[2]
pytestmark = pytest.mark.skipif(
    shutil.which('lake') is None or not (ROOT / '.lake' / 'build').is_dir(),
    reason='needs a built Lean workspace (`lake build`)',
)


@pytest.fixture(autouse=True)
def _forget_new_records() -> Iterator[None]:
    """Delete the records a test writes into the repository's workspace."""
    before = set(RecordStore(ROOT).all())
    yield
    for path in set(RecordStore(ROOT).all()) - before:
        path.unlink()


def test_check_reports_axioms(tmp_path: Path) -> None:
    """Accept a file that type-checks, and give each declaration its axioms, `sorry` included."""
    path = tmp_path / 'Good.lean'
    path.write_text('theorem good : 1 + 1 = 2 := rfl\n\ntheorem gap : 1 = 1 := sorry\n')
    record = run_step(CHECK, ROOT, {'file': str(path)}, rerun=True).record
    assert record.status == 'accepted'
    assert record.outputs['axioms'] == {'gap': ['sorryAx'], 'good': []}


def test_check_refuses_a_broken_file(tmp_path: Path) -> None:
    """Refuse a file that does not type-check, with Lean's error at the file's own line, and exit with status 1."""
    path = tmp_path / 'Broken.lean'
    path.write_text('-- a false claim\ntheorem bad : 1 = 2 := rfl\n')
    record = run_step(CHECK, ROOT, {'file': str(path)}, rerun=True).record
    errors = record.outputs['errors']
    assert record.status == 'refused'
    assert isinstance(errors, list)
    assert errors[0]['line'] == 2
    with pytest.raises(SystemExit) as raised:
        main(['--root', str(ROOT), 'check', str(path)])
    assert raised.value.code == 1


def test_level_matches_the_lean_report() -> None:
    """Report the levels `#veriphy_levels` gives the kit's level fixtures."""
    record = run_step(LEVEL, ROOT, {'module': 'VeriphyTest.Kit', 'prefixes': ['KitLevels']}, rerun=True).record
    assert record.status == 'reported'
    assert record.outputs['levels'] == {
        'KitLevels.axiomOne': 'none',
        'KitLevels.certifiedOnAxiom': 'none',
        'KitLevels.certifiedOne': 'certificate',
        'KitLevels.plainOne': 'lean-proof',
        'KitLevels.sorriedOne': 'none',
        'KitLevels.testedOne': 'kernel-test',
    }
