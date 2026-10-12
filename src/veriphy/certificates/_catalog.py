"""List and show the certificate scripts saved in a project."""

import sys
from collections.abc import Sequence
from pathlib import Path

HEADER_KEYS = ('name', 'technique', 'goal', 'description')
DEFAULT_DIR = 'certificates'
USAGE = 'usage: python -m veriphy.certificates list [dir] | show <name> [dir]\n'
BAD_USAGE = 2
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


def _describe(path: Path) -> str:
    """Return one catalog line for a script, noting header keys it lacks."""
    header = _read_header(path)
    fields = [header.get(key, '') for key in HEADER_KEYS]
    fields[0] = fields[0] or path.stem
    missing = [key for key in HEADER_KEYS if key not in header]
    note = f'  (incomplete header: missing {", ".join(missing)})' if missing else ''
    return ' | '.join(fields) + note


def _find(directory: Path, name: str) -> Path | None:
    """Return the script whose header name or file stem is `name`."""
    for path in _scripts(directory):
        if name in (path.stem, _read_header(path).get('name')):
            return path
    return None


def main(argv: Sequence[str] | None = None) -> None:
    """List the project's certificate scripts, or show one, as `list [dir]` or `show <name> [dir]`."""
    args = list(sys.argv[1:] if argv is None else argv)
    if args[:1] == ['list'] and len(args) <= len(['list', 'dir']):
        directory = Path(args[1] if len(args) > 1 else DEFAULT_DIR)
        sys.stdout.write(''.join(f'{_describe(p)}\n' for p in _scripts(directory)))
        return
    if args[:1] == ['show'] and len(args) in (len(['show', 'name']), len(['show', 'name', 'dir'])):
        directory = Path(args[2] if len(args) > len(['show', 'name']) else DEFAULT_DIR)
        found = _find(directory, args[1])
        if found is None:
            sys.stderr.write(f"no certificate script named '{args[1]}' in {directory}/\n")
            raise SystemExit(NOT_FOUND)
        sys.stdout.write(found.read_text())
        return
    sys.stderr.write(USAGE)
    raise SystemExit(BAD_USAGE)
