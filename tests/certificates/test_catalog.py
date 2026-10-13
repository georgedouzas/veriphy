"""Test the certificate-script catalog."""

from pathlib import Path

import pytest

from veriphy.certificates import main

COMPLETE = (
    '# name: farkas_anomaly\n# technique: farkas\n# goal: False from linear hypotheses\n# description: Refute.\nx = 1\n'
)
INCOMPLETE = '# name: square_hint\n# goal: 0 ≤ p\nproof = None\n'


def _write_scripts(directory: Path) -> None:
    """Write a complete and an incomplete script, and a non-script file, into `directory`."""
    directory.mkdir(parents=True)
    (directory / 'farkas.sage').write_text(COMPLETE)
    (directory / 'hint.sage').write_text(INCOMPLETE)
    (directory / 'notes.txt').write_text('not a script')


@pytest.fixture
def project(tmp_path: Path) -> Path:
    """Return a workspace root whose `.veriphy/certificates/` holds two scripts."""
    (tmp_path / 'lakefile.toml').write_text('')
    _write_scripts(tmp_path / '.veriphy' / 'certificates')
    return tmp_path


@pytest.fixture
def legacy_project(tmp_path: Path) -> Path:
    """Return a workspace root with its scripts in the 0.1.0 `certificates/` directory."""
    (tmp_path / 'lakefile.toml').write_text('')
    _write_scripts(tmp_path / 'certificates')
    return tmp_path


def test_main_list_prints_catalog(project: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """List each script by the name `sage_run file` takes, with its header fields, noting incomplete headers."""
    main(['list', '--root', str(project)])
    captured = capsys.readouterr()
    assert captured.out.splitlines() == [
        'farkas.sage | farkas_anomaly | farkas | False from linear hypotheses | Refute.',
        'hint.sage | square_hint |  | 0 ≤ p |   (incomplete header: missing technique, description)',
    ]
    assert captured.err == ''


def test_main_list_from_a_subdirectory(
    project: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Find the workspace's `.veriphy/` from a subdirectory, with no `--root`."""
    sub = project / 'Physics' / 'Anomaly'
    sub.mkdir(parents=True)
    monkeypatch.chdir(sub)
    main(['list'])
    assert len(capsys.readouterr().out.splitlines()) == 2


def test_main_show_by_header_name_or_stem(project: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Print a script found by its header name or its file stem."""
    main(['show', 'farkas_anomaly', '--root', str(project)])
    assert capsys.readouterr().out == COMPLETE
    main(['show', 'hint', '--root', str(project)])
    assert capsys.readouterr().out == INCOMPLETE


def test_main_show_missing(project: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Exit with status 1 and name the missing script."""
    with pytest.raises(SystemExit) as exit_info:
        main(['show', 'nope', '--root', str(project)])
    assert exit_info.value.code == 1
    assert "'nope'" in capsys.readouterr().err


def test_main_list_without_scripts(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """List nothing, and create nothing, for a project without scripts."""
    (tmp_path / 'lakefile.toml').write_text('')
    main(['list', '--root', str(tmp_path)])
    assert capsys.readouterr().out == ''
    assert not (tmp_path / '.veriphy').exists()


def test_main_list_legacy_layout_warns(legacy_project: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """List 0.1.0 scripts by their runnable path, and print the command that moves them."""
    main(['list', '--root', str(legacy_project)])
    captured = capsys.readouterr()
    assert captured.out.splitlines()[0].startswith('certificates/farkas.sage | farkas_anomaly')
    assert 'git mv certificates .veriphy/certificates' in captured.err


def test_main_bad_usage(capsys: pytest.CaptureFixture[str]) -> None:
    """Exit with status 2 and the usage line."""
    with pytest.raises(SystemExit) as exit_info:
        main(['frobnicate'])
    assert exit_info.value.code == 2
    assert 'usage' in capsys.readouterr().err
