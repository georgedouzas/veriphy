"""The Lean steps, `check` and `level`, over the `lean` pack's primitives, and what a Lean step's digest covers."""

from pathlib import Path

from veriphy.core import canonical_json, content_digest
from veriphy.steps import Argument, Outcome, Params, Prepared, Step, call_primitive


def lean_sources(root: Path) -> str:
    """Return the content a Lean step's digest covers: every Lean file of the workspace, the toolchain and manifest.

    Hidden directories, which hold `.lake/` and Veriphy's own records, are skipped.

    Args:
        root: The workspace root.

    Returns:
        Canonical JSON naming each file with the digest of its content.
    """
    files = {
        str(path.relative_to(root)): content_digest(path.read_bytes())
        for path in sorted(root.rglob('*.lean'))
        if not any(part.startswith('.') for part in path.relative_to(root).parts)
    }
    for name in ('lean-toolchain', 'lake-manifest.json'):
        if (root / name).is_file():
            files[name] = content_digest((root / name).read_bytes())
    return canonical_json(files)


def resolve(root: Path, file: object) -> Path:
    """Return a file parameter as a path, relative ones taken from the workspace root."""
    path = Path(str(file))
    return path if path.is_absolute() else root / path


def _prepare_check(root: Path, params: Params) -> Prepared:
    """Read the file and the workspace's Lean sources."""
    path = resolve(root, params['file'])
    return Prepared(
        {'file': path.read_bytes(), 'workspace': lean_sources(root)},
        {'file': str(path)},
        context=path,
    )


def _check(root: Path, _params: Params, prepared: Prepared) -> Outcome:
    """Have Lean check the file, and report its errors and the axioms of each declaration (`lean.check`)."""
    path = prepared.context if isinstance(prepared.context, Path) else Path()
    return call_primitive(root, 'lean.check', {'root': str(root), 'file': str(path)})


def _prepare_level(root: Path, params: Params) -> Prepared:
    """Read the module, the prefixes and the workspace's Lean sources."""
    module = str(params['module'])
    raw = params.get('prefixes')
    prefixes = [str(p) for p in raw] if isinstance(raw, list | tuple) and raw else [module]
    contents = {'workspace': lean_sources(root), 'module': module, 'prefixes': canonical_json(prefixes)}
    return Prepared(contents, {'module': module, 'prefixes': prefixes}, context=prefixes)


def _level(root: Path, params: Params, prepared: Prepared) -> Outcome:
    """Build the module, then report each declaration's level under the prefixes (`lean.level`)."""
    prefixes = prepared.context if isinstance(prepared.context, list) else [str(params['module'])]
    inputs: dict[str, object] = {'root': str(root), 'module': str(params['module']), 'prefixes': prefixes}
    return call_primitive(root, 'lean.level', inputs)


CHECK = Step(
    'check',
    'check',
    _prepare_check,
    _check,
    help='Lean checks a file, with each axiom set',
    arguments=(Argument('file'),),
)
LEVEL = Step(
    'level',
    'derived',
    _prepare_level,
    _level,
    help='the levels of a module, from #veriphy level',
    arguments=(
        Argument('module'),
        Argument('prefixes', 'a name prefix (default: the module)', option=True, flag='--prefix', many=True),
    ),
)
