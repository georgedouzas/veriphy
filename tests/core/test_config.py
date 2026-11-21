"""Test the workspace configuration: `veriphy.yaml`, packs in the order they require, and JSON Merge Patch."""

import json
from pathlib import Path

import pytest

from veriphy.__main__ import main as veriphy_main
from veriphy.core import PackError, check_config, merge_patch, resolve
from veriphy.primitives import load_registry
from veriphy.steps import config_digest, load_steps


def main(argv: list[str]) -> None:
    """Run `veriphy config` with the arguments."""
    veriphy_main(['config', *argv])


ECON = """version: 1
name: econ
requires: [core]
primitives:
  econ.mean:
    function: statistics:fmean
    trust: reproduction
    input: {type: object}
    output: {type: object}
"""


def _workspace(tmp_path: Path, text: str | None = None) -> Path:
    """Return a workspace root, with `veriphy.yaml` holding `text` when given."""
    (tmp_path / 'lakefile.toml').write_text('')
    if text is not None:
        (tmp_path / 'veriphy.yaml').write_text(text)
    return tmp_path


def test_no_file_selects_math(tmp_path: Path) -> None:
    """Resolve a workspace without `veriphy.yaml` to the `math` pack and the packs it requires, in order."""
    resolved = resolve(_workspace(tmp_path))
    assert [p.name for p in resolved.packs] == ['core', 'lean', 'math']
    assert {'sage', 'lean.check', 'horn.check'} <= set(resolved.section('tools')) | set(resolved.section('primitives'))


def test_a_typo_names_the_key(tmp_path: Path) -> None:
    """Refuse an unknown key, naming it."""
    with pytest.raises(PackError, match="'tool' was unexpected"):
        resolve(_workspace(tmp_path, 'version: 1\ntool: {}\n'))


def test_a_wrong_type_names_its_path(tmp_path: Path) -> None:
    """Refuse a value of the wrong type, naming where it is."""
    with pytest.raises(PackError, match='packs'):
        resolve(_workspace(tmp_path, 'version: 1\npacks: math\n'))


def test_a_local_pack_without_lean(tmp_path: Path) -> None:
    """Load a pack by path, with its requirements first, and nothing of Lean or Sage."""
    root = _workspace(tmp_path, 'version: 1\npacks: [./packs/econ]\n')
    (root / 'packs' / 'econ').mkdir(parents=True)
    (root / 'packs' / 'econ' / 'pack.yaml').write_text(ECON)
    resolved = resolve(root)
    assert [p.name for p in resolved.packs] == ['core', 'econ']
    registry = load_registry(resolved=resolved)
    assert 'econ.mean' in registry.primitives
    assert not any(name.startswith(('sage.', 'lean.')) for name in registry.primitives)


def test_unknown_and_missing_packs(tmp_path: Path) -> None:
    """Refuse an unknown pack name, and a pack requiring a pack that does not exist, naming them."""
    with pytest.raises(PackError, match="no pack is named 'nosuch'"):
        resolve(_workspace(tmp_path, 'version: 1\npacks: [nosuch]\n'))
    (tmp_path / 'lonely').mkdir()
    (tmp_path / 'lonely' / 'pack.yaml').write_text('version: 1\nname: lonely\nrequires: [absent]\n')
    with pytest.raises(PackError, match="no pack is named 'absent'"):
        resolve(_workspace(tmp_path, 'version: 1\npacks: [./lonely]\n'))


def test_merge_patch_follows_rfc_7396() -> None:
    """Merge as RFC 7396's own example does."""
    target = {'title': 'Goodbye!', 'author': {'givenName': 'John', 'familyName': 'Doe'}, 'tags': ['example', 'sample']}
    patch = {'title': 'Hello!', 'phoneNumber': '+01-123-456-7890', 'author': {'familyName': None}, 'tags': ['example']}
    assert merge_patch(target, patch) == {
        'title': 'Hello!',
        'author': {'givenName': 'John'},
        'tags': ['example'],
        'phoneNumber': '+01-123-456-7890',
    }


def test_null_removes_a_tool(tmp_path: Path) -> None:
    """Drop SageMath with `tools: {sage: null}`, leaving its primitives unavailable, and refused by the check."""
    resolved = resolve(_workspace(tmp_path, 'version: 1\ntools: {sage: null}\n'))
    assert 'sage' not in resolved.section('tools')
    registry = load_registry(resolved=resolved)
    assert "its tool 'sage' is not declared" in str(registry.unavailable('sage.sample'))
    assert any("primitives.sage.sample names the tool 'sage'" in p for p in check_config(resolved))


def test_collisions_and_how_the_workspace_settles_them(tmp_path: Path) -> None:
    """Refuse an entry two unrelated packs define, naming both, until the workspace file defines it."""
    for name in ('one', 'two'):
        (tmp_path / name).mkdir()
        (tmp_path / name / 'pack.yaml').write_text(ECON.replace('econ', name).replace(f'{name}.mean', 'shared.mean'))
    resolved = resolve(_workspace(tmp_path, 'version: 1\npacks: [./one, ./two]\n'))
    assert resolved.collisions == (('primitives.shared.mean', 'one', 'two'),)
    assert 'defined by one and by two' in check_config(resolved)[0]
    settle = 'primitives:\n  shared.mean: {function: statistics:fmean, trust: oracle, input: {}, output: {}}\n'
    settled = resolve(_workspace(tmp_path, 'version: 1\npacks: [./one, ./two]\n' + settle))
    assert settled.collisions == ()
    assert settled.sources['primitives.shared.mean'] == 'veriphy.yaml'


def test_selected_packs_select_steps(tmp_path: Path) -> None:
    """Give a workspace of `core` alone the graph steps and no Lean step."""
    steps = load_steps(_workspace(tmp_path, 'version: 1\npacks: [core]\n'))
    assert {'validate', 'reason', 'report'} <= set(steps)
    assert not {'check', 'level', 'meaning'} & set(steps)


def test_config_digest_follows_meaning(tmp_path: Path) -> None:
    """Change the config digest with a pin, and keep it through a comment."""
    root = _workspace(tmp_path, 'version: 1\n')
    before = config_digest(root)
    (root / 'veriphy.yaml').write_text('# a comment\nversion: 1\n')
    assert config_digest(root) == before
    (root / 'veriphy.yaml').write_text('version: 1\ntools: {sage: {pin: {version: "10.8"}}}\n')
    assert config_digest(root) != before


def test_show_names_each_source(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Show the resolved configuration with the pack or file each entry comes from, and pass the check."""
    root = _workspace(tmp_path, 'version: 1\ntools: {sage: {pin: {version: "10.9"}}}\n')
    main(['--root', str(root), 'show'])
    shown = json.loads(capsys.readouterr().out)
    assert shown['packs'] == ['core', 'lean', 'math']
    assert (shown['sources']['tools.sage'], shown['sources']['primitives.lean.check']) == ('veriphy.yaml', 'lean')
    assert shown['config']['tools']['sage']['contract'] == 'files'
    main(['--root', str(root), 'check'])
    assert 'no problems' in capsys.readouterr().out
