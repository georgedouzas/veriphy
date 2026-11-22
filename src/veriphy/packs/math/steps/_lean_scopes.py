"""The `lean` pack's digest scopes: what a Lean file stands for, with its imports, and a whole workspace."""

import re
from pathlib import Path

from veriphy.core import canonical_json, content_digest

IMPORT = re.compile(r'^import\s+([\w.]+)', re.MULTILINE)
CONTEXT = ('lean-toolchain', 'lake-manifest.json')


def _visible(root: Path, path: Path) -> bool:
    """Return whether a file belongs to the workspace's sources, outside hidden directories such as `.lake/`."""
    return not any(part.startswith('.') for part in path.relative_to(root).parts)


def _modules(root: Path) -> dict[str, Path]:
    """Return every Lean file of the workspace by each module name it can be imported as."""
    found: dict[str, Path] = {}
    for path in sorted(root.rglob('*.lean')):
        if not _visible(root, path):
            continue
        parts = path.relative_to(root).with_suffix('').parts
        for start in range(len(parts)):
            found.setdefault('.'.join(parts[start:]), path)
    return found


def _context(root: Path) -> dict[str, str]:
    """Return the digests of the toolchain and the manifest, which stand for everything outside the workspace."""
    return {name: content_digest((root / name).read_bytes()) for name in CONTEXT if (root / name).is_file()}


def lean_imports(root: Path, value: object) -> str:
    """Return what a Lean file stands for: its content, every workspace file it imports, the toolchain and manifest.

    Args:
        root: The workspace root.
        value: The file.

    Returns:
        Canonical JSON of the digests; an edit to a file it does not import leaves it unchanged.
    """
    modules = _modules(root)
    start = Path(str(value))
    seen: dict[str, str] = {}
    pending = [start]
    while pending:
        path = pending.pop()
        key = str(path.relative_to(root)) if path.is_relative_to(root) else str(path)
        if key in seen:
            continue
        text = path.read_text()
        seen[key] = content_digest(text)
        pending.extend(modules[m] for m in IMPORT.findall(text) if m in modules)
    return canonical_json({'files': seen, **_context(root)})


def lean_workspace(root: Path, value: object) -> str:
    """Return what a workspace's Lean sources stand for, with the value named: every Lean file, toolchain, manifest.

    Args:
        root: The workspace root.
        value: What the step names in it, such as a module.

    Returns:
        Canonical JSON of the digests.
    """
    files = {
        str(p.relative_to(root)): content_digest(p.read_bytes())
        for p in sorted(root.rglob('*.lean'))
        if _visible(root, p)
    }
    return canonical_json({'value': value, 'files': files, **_context(root)})
