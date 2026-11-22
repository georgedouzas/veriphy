"""Test that the documentation's console sessions print what the CLI prints, and that it uses every command."""

import shutil
from collections.abc import Iterator
from pathlib import Path

import click
import pytest

from tests.docs.sessions import ROOT, make_workspace, matches, read_commands, run_command
from veriphy.__main__ import veriphy
from veriphy.claims import find_checker
from veriphy.core import BUILTIN_PACKS
from veriphy.steps._registry import step_packs

DOCS = ROOT / 'docs'
PAGES = [DOCS / 'overview' / name for name in ('getting_started.md', 'tutorial.md', 'user_guide.md')]
STEP_GROUP = 'veriphy layers step'
GENERIC = {f'{STEP_GROUP} list', f'{STEP_GROUP} records'}
INSTALL = ('pip ', 'sage -pip ')
TUTORIAL = DOCS / 'overview' / 'tutorial.md'
MATH = DOCS / 'packs' / 'math.md'
# commands whose use needs files only the math pack ships, so its page shows them
MATH_ONLY = {'veriphy layers agents copy'}
# pages whose sessions need a Lean project, or are guides with no session of their own
UNRUN = {'math', 'math_components', 'index'}
# pages whose sessions run their code under SageMath
SAGE = {'number_theory', 'group_theory', 'graph_theory'}
SAGE_SESSION = ROOT / 'src' / 'veriphy' / 'packs' / 'math' / 'primitives' / 'sage' / '__main__.py'
PACK_PAGES = sorted(p for p in (DOCS / 'packs').glob('*.md') if p.stem not in UNRUN)


def _checker_ready() -> bool:
    """Return whether `oo-horn` is set up, which the claim graph's sessions need."""
    path = find_checker().path
    return path is not None and path.is_file()


def _check_page(page: Path, workspace: Path) -> None:
    """Run a page's commands in order in a workspace, and match each output with the page's."""
    for command in read_commands(page):
        if command.text.startswith(INSTALL):
            continue
        actual = run_command(command, workspace).replace(str(workspace.resolve()), '…')
        assert matches(command.expected, actual), f'{page.name}:{command.line}: $ {command.text}\n{actual}'


@pytest.mark.parametrize('page', PAGES, ids=lambda page: page.stem)
def test_console_sessions_print_what_the_cli_prints(page: Path, tmp_path: Path) -> None:
    """Run an overview page's commands in order in the example study, and match each output with the page's."""
    if not _checker_ready():
        pytest.skip('oo-horn is not built: veriphy layers claims checker build')
    _check_page(page, make_workspace(tmp_path))


@pytest.mark.parametrize('page', PACK_PAGES, ids=lambda page: page.stem)
def test_pack_pages_print_what_the_cli_prints(page: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Run a pack page's commands in a workspace that selects the pack and holds its examples."""
    if page.stem in SAGE:
        if shutil.which('sage') is None:
            pytest.skip('the page runs its code under SageMath')
        # Sage's own Python runs the subfields' functions, from this tree
        monkeypatch.setenv('VERIPHY_SAGE_SESSION', str(SAGE_SESSION))
        monkeypatch.setenv('PYTHONPATH', str(ROOT / 'src'))
    if '$ veriphy layers step reason' in page.read_text() and not _checker_ready():
        pytest.skip('oo-horn is not built: veriphy layers claims checker build')
    pack = page.stem.replace('_', '-')
    _check_page(page, make_workspace(tmp_path, pack, select=True))


def _paths(command: click.Command, ctx: click.Context, prefix: str) -> Iterator[str]:
    """Yield the command paths below a command, each as it is typed."""
    if not isinstance(command, click.Group):
        yield prefix
        return
    for name in command.list_commands(ctx):
        child = command.get_command(ctx, name)
        if child is not None:
            yield from _paths(child, click.Context(child, parent=ctx, info_name=name), f'{prefix} {name}')


def _commands(packs: list[str], workspace: Path) -> set[str]:
    """Return every command path of a workspace that selects the packs."""
    (workspace / 'veriphy.yaml').write_text(f'version: 1\npacks: [{", ".join(packs)}]\n')
    ctx = click.Context(veriphy, info_name='veriphy')
    ctx.params['root'] = workspace
    declared = {f'{STEP_GROUP} {name}' for name in step_packs(workspace)}
    # a step another test registers in code belongs to no pack, so no page documents it
    return {p for p in _paths(veriphy, ctx, 'veriphy') if not p.startswith(f'{STEP_GROUP} ') or p in declared | GENERIC}


def test_tutorial_uses_every_command(tmp_path: Path) -> None:
    """Find every command of a workspace without the math pack in the tutorial, or on the math page."""
    tutorial, math = TUTORIAL.read_text(), MATH.read_text()
    missing = [c for c in sorted(_commands(['social-science'], tmp_path)) if c not in tutorial]
    assert [c for c in missing if c not in MATH_ONLY] == []
    assert [c for c in MATH_ONLY if c not in math] == []


@pytest.mark.parametrize('pack', BUILTIN_PACKS)
def test_pack_commands_appear_in_the_docs(pack: str, tmp_path: Path) -> None:
    """Find every step and program a shipped pack adds on the pages of the packs or in the tutorial."""
    if pack == 'core':
        pytest.skip('the tutorial covers the core pack')
    pages = '\n'.join(p.read_text() for p in [TUTORIAL, *(DOCS / 'packs').glob('*.md')])
    (tmp_path / 'core').mkdir()
    (tmp_path / pack).mkdir()
    added = _commands([pack], tmp_path / pack) - _commands(['core'], tmp_path / 'core')
    assert [c for c in sorted(added) if c not in pages] == []
