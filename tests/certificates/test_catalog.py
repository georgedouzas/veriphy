"""Test the certificate-script catalog."""

from pathlib import Path

import pytest

from veriphy.certificates import main

COMPLETE = (
    '# name: farkas_anomaly\n# technique: farkas\n# goal: False from linear hypotheses\n# description: Refute.\nx = 1\n'
)
INCOMPLETE = '# name: square_hint\n# goal: 0 ≤ p\nproof = None\n'


@pytest.fixture
def project(tmp_path: Path) -> Path:
    """Return a directory holding a complete and an incomplete script, and a non-script file."""
    (tmp_path / 'farkas.sage').write_text(COMPLETE)
    (tmp_path / 'hint.sage').write_text(INCOMPLETE)
    (tmp_path / 'notes.txt').write_text('not a script')
    return tmp_path


def test_main_list_prints_catalog(project: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """List each script with its header fields and note incomplete headers."""
    main(['list', str(project)])
    lines = capsys.readouterr().out.splitlines()
    assert lines == [
        f'{project / "farkas.sage"} | farkas_anomaly | farkas | False from linear hypotheses | Refute.',
        f'{project / "hint.sage"} | square_hint |  | 0 ≤ p |   (incomplete header: missing technique, description)',
    ]


def test_main_show_by_header_name_or_stem(project: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Print a script found by its header name or its file stem."""
    main(['show', 'farkas_anomaly', str(project)])
    assert capsys.readouterr().out == COMPLETE
    main(['show', 'hint', str(project)])
    assert capsys.readouterr().out == INCOMPLETE


def test_main_show_missing(project: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Exit with status 1 and name the missing script."""
    with pytest.raises(SystemExit) as exit_info:
        main(['show', 'nope', str(project)])
    assert exit_info.value.code == 1
    assert "'nope'" in capsys.readouterr().err


def test_main_list_missing_directory(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """List nothing for a project without a certificates directory."""
    main(['list', str(tmp_path / 'absent')])
    assert capsys.readouterr().out == ''


def test_main_bad_usage(capsys: pytest.CaptureFixture[str]) -> None:
    """Exit with status 2 and the usage line."""
    with pytest.raises(SystemExit) as exit_info:
        main(['frobnicate'])
    assert exit_info.value.code == 2
    assert 'usage' in capsys.readouterr().err
