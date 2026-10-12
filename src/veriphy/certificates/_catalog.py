"""List and show the certificate scripts saved in a project's `.veriphy/certificates/`."""

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from veriphy.core import find_workspace_root, project_dir

HEADER_KEYS = ('name', 'technique', 'goal', 'description')
SCRIPTS_DIR = 'certificates'
LEGACY_DIR = 'certificates'
NOT_FOUND = 1


def _read_header(path: Path) -> dict[str, str]:
    """Return the `# key: value` lines at the top of a script, up to its first other line."""
    header: dict[str, str] = {}
    for line in path.read_text().splitlines():
        if not line.startswith('#'):
            break
        key, sep, value = line.lstrip('#').strip().partition(':')
        if sep and key.strip() in HEADER_KEYS:
            header[key.strip()] = value.strip()
    return header


def _scripts(directory: Path) -> list[Path]:
    """Return the `.sage` scripts in a directory, sorted by file name."""
    return sorted(directory.glob('*.sage')) if directory.is_dir() else []


def _describe(path: Path, runnable: str) -> str:
    """Return one catalog line for a script: what `sage_run file` takes, then its header fields."""
    header = _read_header(path)
    fields = [runnable, *(header.get(key, '') for key in HEADER_KEYS)]
    missing = [key for key in HEADER_KEYS if key not in header]
    note = f'  (incomplete header: missing {", ".join(missing)})' if missing else ''
    return ' | '.join(fields) + note


def _find(directory: Path, name: str) -> Path | None:
    """Return the script whose header name or file stem is `name`."""
    for path in _scripts(directory):
        if name in (path.stem, _read_header(path).get('name')):
            return path
    return None


def _scripts_dir(root: Path) -> tuple[Path, bool]:
    """Return the directory holding the project's scripts, and whether it is the 0.1.0 layout."""
    current = project_dir(root) / SCRIPTS_DIR
    legacy = root / LEGACY_DIR
    if not current.is_dir() and _scripts(legacy):
        return legacy, True
    return current, False


def _warn_legacy(root: Path) -> None:
    """Tell the user that scripts moved to `.veriphy/certificates/`, with the command that moves them."""
    message = (
        f'warning: scripts in {root / LEGACY_DIR}/ use the 0.1.0 layout; they belong in .veriphy/{SCRIPTS_DIR}/.\n'
        f'  move them with: mkdir -p .veriphy && git mv {LEGACY_DIR} .veriphy/{SCRIPTS_DIR}\n'
    )
    sys.stderr.write(message)


def _parser() -> argparse.ArgumentParser:
    """Return the command-line parser: `list [--root DIR]` and `show <name> [--root DIR]`."""
    parser = argparse.ArgumentParser(prog='python -m veriphy.certificates')
    commands = parser.add_subparsers(dest='command', required=True)
    for command in (commands.add_parser('list'), commands.add_parser('show')):
        command.add_argument('--root', type=Path, default=None, help='the Lean workspace root (found by default)')
    commands.choices['show'].add_argument('name')
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    """List the project's certificate scripts, or show one, as `list [--root DIR]` or `show <name> [--root DIR]`.

    Args:
        argv: The command-line arguments, `sys.argv[1:]` when `None`.

    Raises:
        SystemExit: With status 1 when `show` finds no script of that name, and 2 on bad usage.
    """
    args = _parser().parse_args(list(sys.argv[1:] if argv is None else argv))
    root = find_workspace_root(args.root)
    directory, legacy = _scripts_dir(root)
    if legacy:
        _warn_legacy(root)
    if args.command == 'list':
        prefix = f'{LEGACY_DIR}/' if legacy else ''
        sys.stdout.write(''.join(f'{_describe(p, prefix + p.name)}\n' for p in _scripts(directory)))
        return
    found = _find(directory, args.name)
    if found is None:
        sys.stderr.write(f"no certificate script named '{args.name}' in {directory}/\n")
        raise SystemExit(NOT_FOUND)
    sys.stdout.write(found.read_text())
