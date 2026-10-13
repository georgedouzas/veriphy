"""Test the translation-entry catalog."""

import shutil
from pathlib import Path

import pytest

from veriphy.translations import main

FIXTURES = Path(__file__).resolve().parents[2] / 'VeriphyTest' / 'fixtures' / 'translations'


@pytest.fixture
def project(tmp_path: Path) -> Path:
    """Return a workspace whose `.veriphy/translations/` holds the Lean suite's fixture files."""
    (tmp_path / 'lakefile.toml').write_text('')
    shutil.copytree(FIXTURES, tmp_path / '.veriphy' / 'translations')
    return tmp_path


def test_list_prints_project_entries_and_reports_invalid_files(
    project: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """List each valid entry under the project namespace, and report the invalid files without failing."""
    main(['list', '--root', str(project)])
    captured = capsys.readouterr()
    assert captured.out.splitlines() == [
        'project | translations/gamma.json | Real.Gamma | gamma | pos #0',
        'project | translations/gamma.json | rw [Real.Gamma_add_one] | Real.Gamma | #0 ≠ 0',
        'project | translations/override.json | Real.exp | myexp |   (conflicts with the mathlib entry; not loaded)',
    ]
    assert "translations/incomplete.json: missing field 'sage'" in captured.err
    assert 'translations/broken.json: not valid JSON' in captured.err


def test_list_all_includes_the_core_and_packs(project: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """With `--all`, list the core and the shipped packs ahead of the project."""
    main(['list', '--all', '--root', str(project)])
    lines = capsys.readouterr().out.splitlines()
    assert lines[0].startswith('mathlib | core_table.json | Real.sqrt | sqrt | nonneg #0')
    assert any(line.startswith('physlib | packs/physlib.json | Time.deriv | diff (derivative)') for line in lines)
    assert lines[-1].startswith('project |')


def test_show_prints_one_entry(project: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Show an entry in full, from any namespace."""
    main(['show', 'Real.Gamma', '--root', str(project)])
    assert capsys.readouterr().out.startswith('namespace: project\nfile: translations/gamma.json\nFunctionEntry(')
    main(['show', 'Real.arcsin', '--root', str(project)])
    assert 'le' in capsys.readouterr().out


def test_show_missing(project: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Exit with status 1 and name the missing entry."""
    with pytest.raises(SystemExit) as exit_info:
        main(['show', 'Real.nothing', '--root', str(project)])
    assert exit_info.value.code == 1
    assert "'Real.nothing'" in capsys.readouterr().err
