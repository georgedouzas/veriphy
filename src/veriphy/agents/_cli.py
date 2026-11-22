"""Find, show and copy the playbooks, recipes, templates and recipe assets the package installs."""

import difflib
import shutil
import sys
from pathlib import Path

import click

from veriphy.core import find_workspace_root, project_dir

SUFFIXES = ('.md', '.sage', '.lean')
ASSETS = 'assets'
NOT_FOUND = 1


def content_dir(pack: str = 'math') -> Path:
    """Return the directory holding a pack's playbooks and recipes.

    Args:
        pack: The pack, `math` by default, whose playbooks are `prove`, `certify` and `research`.

    Returns:
        The installed `veriphy/packs/<pack>/agents/` directory.

    Examples:
        >>> (content_dir() / 'prove.md').is_file()
        True
    """
    # a pack's name may hold a dash, its package an underscore
    return Path(__file__).resolve().parents[1] / 'packs' / pack.replace('-', '_') / 'agents'


def assets_dir() -> Path:
    """Return the directory holding the recipe assets: the math pack's Lean sources, where Lake builds them too.

    Returns:
        The directory whose `VeriphyAssets/` holds the asset files.

    Examples:
        >>> (assets_dir() / 'VeriphyAssets' / 'FusionData.lean').is_file()
        True
    """
    return Path(__file__).resolve().parents[1] / 'packs' / 'math' / 'lean' / ASSETS


def entries() -> dict[str, Path]:
    """Return every playbook, recipe, template and asset, keyed by its name relative to the content directory.

    Returns:
        The files, keyed by names such as `prove.md`, `recipes/templates/sos.sage` and
        `assets/VeriphyAssets/FusionData.lean`, sorted by name.

    Examples:
        >>> names = entries()
        >>> 'prove.md' in names and 'recipes/templates/sos.sage' in names
        True
        >>> 'assets/VeriphyAssets/FusionData.lean' in names
        True
    """
    base, assets = content_dir(), assets_dir()
    found = {
        p.relative_to(base).as_posix(): p
        for p in base.rglob('*')
        if p.suffix in SUFFIXES and p.is_file() and ASSETS not in p.relative_to(base).parts
    }
    shipped = assets / 'VeriphyAssets'
    found |= {f'{ASSETS}/{p.relative_to(assets).as_posix()}': p for p in shipped.rglob('*.lean') if p.is_file()}
    return dict(sorted(found.items()))


def _resolve(name: str) -> tuple[str, Path]:
    """Return the entry a name denotes, with the extension optional, or exit naming the closest matches."""
    known = entries()
    matches = [key for key in known if name in (key, key.rsplit('.', 1)[0])]
    if len(matches) == 1:
        return matches[0], known[matches[0]]
    if matches:
        message = f"'{name}' is ambiguous: {', '.join(matches)}\n"
    else:
        stems = {key.rsplit('.', 1)[0]: key for key in known}
        close = difflib.get_close_matches(name, list(stems), n=3)
        message = f"no playbook, recipe, template or asset named '{name}'"
        message += f"; closest: {', '.join(stems[c] for c in close)}\n" if close else '\n'
    sys.stderr.write(message)
    raise SystemExit(NOT_FOUND)


def _destination(key: str, root: Path) -> Path:
    """Return where `copy` puts an entry: templates in `.veriphy/certificates/`, assets in `.veriphy/lean/`."""
    if key.endswith('.sage'):
        return project_dir(root) / 'certificates' / Path(key).name
    if key.startswith(f'{ASSETS}/'):
        return project_dir(root) / 'lean' / Path(key).relative_to(ASSETS)
    sys.stderr.write(f"'{key}' is neither a template nor an asset, so it is read in place: use `show`\n")
    raise SystemExit(NOT_FOUND)


def _copy(name: str, root: Path) -> None:
    """Copy a template or an asset into the workspace, refusing to overwrite a file."""
    key, source = _resolve(name)
    target = _destination(key, root)
    if target.exists():
        sys.stderr.write(f'{target} already exists; nothing was copied\n')
        raise SystemExit(NOT_FOUND)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    sys.stdout.write(f'{target}\n')


@click.group(name='agents', help='The playbooks, recipes, templates and recipe assets the package installs.')
def agents() -> None:
    """Give an agent the installed playbooks."""


@agents.command(help="print the directory holding a pack's playbooks and recipes")
@click.option('--pack', default='math', help='the pack (default: math)')
def path(pack: str) -> None:
    """Print the content directory of a pack."""
    sys.stdout.write(f'{content_dir(pack)}\n')


@agents.command(name='list', help='list every playbook, recipe, template and asset')
def list_entries() -> None:
    """List every entry by name."""
    sys.stdout.write(''.join(f'{key}\n' for key in entries()))


@agents.command(help='print one file')
@click.argument('name')
def show(name: str) -> None:
    """Print one entry."""
    sys.stdout.write(_resolve(name)[1].read_text())


@agents.command(help='copy a template or an asset into the workspace')
@click.argument('name')
@click.option(
    '--root',
    type=click.Path(path_type=Path),
    default=None,
    help='the Lean workspace root (found by default)',
)
def copy(name: str, root: Path | None) -> None:
    """Copy a template or an asset into the workspace."""
    _copy(name, find_workspace_root(root))
