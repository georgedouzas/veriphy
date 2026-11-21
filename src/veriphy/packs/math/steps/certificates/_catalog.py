"""List and show the certificate scripts saved in a project's `.veriphy/certificates/`."""

import ast
import sys
from pathlib import Path

import click

from veriphy.core import find_workspace_root, project_dir
from veriphy.packs.math.steps.certificates import _tests as tests

HEADER_KEYS = ('name', 'technique', 'goal', 'description')
SCRIPTS_DIR = 'certificates'
NOT_FOUND = 1
# a rerun oracle instance no longer matches its record
CHANGED = 3


def _declared(text: str) -> dict[str, str] | None:
    """Return the fields of a script's `SCRIPT = {...}` declaration, or `None` when it has none."""
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return None
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'SCRIPT' for t in node.targets):
            try:
                value = ast.literal_eval(node.value)
            except ValueError:
                return None
            return {str(k): str(v) for k, v in value.items()} if isinstance(value, dict) else None
    return None


def _read_header(path: Path) -> dict[str, str]:
    """Return a script's fields: its `SCRIPT` declaration, or else its `# key: value` lines up to the first other."""
    text = path.read_text()
    declared = _declared(text)
    if declared is not None:
        return {key: value for key, value in declared.items() if key in HEADER_KEYS}
    header: dict[str, str] = {}
    for line in text.splitlines():
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
    """Return one catalog line for a script: what `veriphy certify` takes, then its header fields."""
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


def _tests(root: Path, target: str | None) -> None:
    """List the test records with their levels, or rerun one record's oracle instances."""
    if target is None:
        sys.stdout.write(''.join(f'{tests.describe(p)}\n' for p in tests.records(root)))
        return
    path = tests.find(root, target)
    if path is None:
        sys.stderr.write(f"no test record for '{target}' in {root / '.veriphy' / tests.TESTS_DIR}/\n")
        raise SystemExit(NOT_FOUND)
    changes = tests.rerun(path)
    if changes:
        sys.stdout.write(''.join(f'{c}\n' for c in changes))
        raise SystemExit(CHANGED)
    sys.stdout.write(f'{target}: the oracle instances hold as recorded\n')


ROOT_OPTION = click.option(
    '--root',
    type=click.Path(path_type=Path),
    default=None,
    help='the Lean workspace root (found by default)',
)


@click.group(name='certificates', help="The project's saved certificate scripts, and its test records.")
def certificates() -> None:
    """Catalog the project's certificate scripts."""


def _directory(root: Path) -> Path:
    """Return the directory of the project's scripts, `.veriphy/certificates/`."""
    return project_dir(root) / SCRIPTS_DIR


@certificates.command(name='list', help='each script, with its header fields')
@ROOT_OPTION
def list_scripts(root: Path | None) -> None:
    """List the scripts."""
    workspace = find_workspace_root(root)
    sys.stdout.write(''.join(f'{_describe(p, p.name)}\n' for p in _scripts(_directory(workspace))))


@certificates.command(help='print one script')
@click.argument('name')
@ROOT_OPTION
def show(name: str, root: Path | None) -> None:
    """Print one script, by its header name or file stem."""
    directory = _directory(find_workspace_root(root))
    found = _find(directory, name)
    if found is None:
        sys.stderr.write(f"no certificate script named '{name}' in {directory}/\n")
        raise SystemExit(NOT_FOUND)
    sys.stdout.write(found.read_text())


@certificates.command(name='tests', help='the test records with their levels')
@click.option('--rerun', metavar='TARGET', default=None, help='rerun the oracle part of a record')
@ROOT_OPTION
def tests_command(rerun: str | None, root: Path | None) -> None:
    """List the test records, or rerun one record's oracle instances."""
    _tests(find_workspace_root(root), rerun)
