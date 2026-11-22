"""Test the prompts command: the installed playbooks, recipes, templates and assets, shown and copied."""

from pathlib import Path

import pytest

from veriphy.__main__ import main as veriphy_main
from veriphy.agents import content_dir, entries


def main(argv: list[str]) -> None:
    """Run `veriphy layers agents` with the arguments."""
    veriphy_main(['layers', 'agents', *argv])


def _run(capsys: pytest.CaptureFixture[str], *argv: str) -> str:
    """Run the command and return what it printed."""
    main(list(argv))
    return capsys.readouterr().out


def _workspace(tmp_path: Path) -> Path:
    """Return a Lean workspace root."""
    (tmp_path / 'lakefile.toml').write_text('')
    return tmp_path


def test_path_prints_the_content_directory(capsys: pytest.CaptureFixture[str]) -> None:
    """Print the directory that holds `prove.md`."""
    assert Path(_run(capsys, 'path').strip()) == content_dir()
    assert (content_dir() / 'prove.md').is_file()


def test_list_names_every_kind(capsys: pytest.CaptureFixture[str]) -> None:
    """List playbooks, recipes, templates, library recipes and assets, one per line."""
    names = _run(capsys, 'list').splitlines()
    for name in (
        'prove.md',
        'research/triage.md',
        'recipes/farkas.md',
        'recipes/templates/farkas.sage',
        'recipes/physlib/templates/lorentz_algebra.sage',
        'assets/VeriphyAssets/FusionData.lean',
    ):
        assert name in names
    assert names == sorted(names)


@pytest.mark.parametrize('name', ['recipes/sos', 'recipes/sos.md'])
def test_show_takes_the_extension_or_not(capsys: pytest.CaptureFixture[str], name: str) -> None:
    """Print the SOS recipe, named with or without its extension."""
    assert _run(capsys, 'show', name) == (content_dir() / 'recipes' / 'sos.md').read_text()


def test_show_unknown_names_the_closest(capsys: pytest.CaptureFixture[str]) -> None:
    """Exit with status 1 for an unknown name, and name the closest entries."""
    with pytest.raises(SystemExit) as raised:
        main(['show', 'recipes/sozz'])
    assert raised.value.code == 1
    assert 'closest: recipes/sos.md' in capsys.readouterr().err


def test_copy_a_template_into_the_workspace(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Copy a template into `.veriphy/certificates/`, found from a subdirectory, and print where it went."""
    root = _workspace(tmp_path)
    (root / 'Sub').mkdir()
    target = root / '.veriphy' / 'certificates' / 'farkas.sage'
    assert Path(_run(capsys, 'copy', 'recipes/templates/farkas', '--root', str(root / 'Sub')).strip()) == target
    assert target.read_text() == entries()['recipes/templates/farkas.sage'].read_text()


def test_copy_an_asset_into_the_workspace(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Copy an asset into `.veriphy/lean/VeriphyAssets/`."""
    root = _workspace(tmp_path)
    _run(capsys, 'copy', 'assets/VeriphyAssets/FusionData', '--root', str(root))
    assert (root / '.veriphy' / 'lean' / 'VeriphyAssets' / 'FusionData.lean').is_file()


def test_copy_refuses_to_overwrite(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Leave an existing script unchanged, name it, and exit with status 1."""
    root = _workspace(tmp_path)
    target = root / '.veriphy' / 'certificates' / 'sos.sage'
    target.parent.mkdir(parents=True)
    target.write_text('mine\n')
    with pytest.raises(SystemExit) as raised:
        main(['copy', 'recipes/templates/sos', '--root', str(root)])
    assert raised.value.code == 1
    assert str(target) in capsys.readouterr().err
    assert target.read_text() == 'mine\n'


def test_copy_refuses_a_playbook(tmp_path: Path) -> None:
    """Refuse to copy a recipe, which is read in place."""
    with pytest.raises(SystemExit) as raised:
        main(['copy', 'recipes/sos', '--root', str(_workspace(tmp_path))])
    assert raised.value.code == 1
    assert not (tmp_path / '.veriphy').exists()


def test_assets_come_from_the_math_packs_lean_sources() -> None:
    """Find the assets in the math pack's Lean sources, where Lake builds them."""
    asset = entries()['assets/VeriphyAssets/FusionData.lean']
    assert asset.is_file()
    assert asset.parts[-5:-2] == ('math', 'lean', 'assets')
