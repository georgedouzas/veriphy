"""Find, show and copy the playbooks, recipes, templates and recipe assets the package installs."""

import argparse
import difflib
import shutil
import sys
from collections.abc import Sequence
from pathlib import Path

from veriphy.core import find_workspace_root, project_dir

SUFFIXES = ('.md', '.sage', '.lean')
ASSETS = 'assets'
NOT_FOUND = 1


def content_dir() -> Path:
    """Return the directory holding the playbooks and recipes.

    Returns:
        The installed `veriphy/packs/math/agents/` directory.

    Examples:
        >>> (content_dir() / 'prove.md').is_file()
        True
    """
    return Path(__file__).resolve().parents[1] / 'packs' / 'math' / 'agents'


def assets_dir() -> Path:
    """Return the directory holding the recipe assets.

    A wheel carries them under `veriphy/packs/math/agents/assets/`. An editable install has no copy, so the repository's
    `lean/assets/`, where Lake builds them, stands in.

    Returns:
        The directory whose `VeriphyAssets/` holds the asset files.

    Examples:
        >>> (assets_dir() / 'VeriphyAssets' / 'FusionData.lean').is_file()
        True
    """
    packaged = content_dir() / ASSETS
    return packaged if packaged.is_dir() else content_dir().parents[4] / 'lean' / ASSETS


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


def _parser() -> argparse.ArgumentParser:
    """Return the command-line parser: `path`, `list`, `show <name>` and `copy <name> [--root DIR]`."""
    parser = argparse.ArgumentParser(prog='veriphy agents')
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('path', help='print the directory holding the playbooks and recipes')
    commands.add_parser('list', help='list every playbook, recipe, template and asset')
    commands.add_parser('show', help='print one file').add_argument('name')
    copy = commands.add_parser('copy', help='copy a template or an asset into the workspace')
    copy.add_argument('name')
    copy.add_argument('--root', type=Path, default=None, help='the Lean workspace root (found by default)')
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    """Give an agent the installed playbooks: `path`, `list`, `show <name>` and `copy <name>`.

    The command exits with status 1 for an unknown or ambiguous name, a copy of a playbook or recipe, or a copy that
    would overwrite a file, and with status 2 on bad usage.

    Args:
        argv: The command-line arguments, `sys.argv[1:]` when `None`.

    Examples:
        >>> main(['show', 'recipes/sos'])  # doctest: +ELLIPSIS
        # ...
    """
    args = _parser().parse_args(list(sys.argv[1:] if argv is None else argv))
    if args.command == 'path':
        sys.stdout.write(f'{content_dir()}\n')
    elif args.command == 'list':
        sys.stdout.write(''.join(f'{key}\n' for key in entries()))
    elif args.command == 'show':
        sys.stdout.write(_resolve(args.name)[1].read_text())
    else:
        _copy(args.name, find_workspace_root(args.root))
