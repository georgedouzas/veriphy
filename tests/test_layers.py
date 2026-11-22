"""Test the layering of the package: a module imports only `veriphy.core` and the layers below its own."""

import ast
import sys
from pathlib import Path

import pytest

from veriphy.core import run_process

SRC = Path(__file__).resolve().parents[1] / 'src'
LAYERS = {'primitives': 0, 'steps': 1, 'claims': 2, 'workflows': 3, 'agents': 4}
CORE = -1
# `veriphy.packs.<pack>.<layer>`: where a pack module names its layer
PACK_LAYER = 3
# modules above the layers, which may import any of them
FACADES = frozenset({'veriphy', 'veriphy.__main__', 'veriphy._api', 'veriphy.script'})


def layer_of(module: str) -> int | None:
    """Return a module's layer: -1 for `veriphy.core`, `None` for the facades.

    A pack's module takes the layer of the layer subpackage it sits in, and a pack's other modules (its `script`
    helpers, its `__init__`) are layer 0.

    Examples:
        >>> layer_of('veriphy.steps._runner'), layer_of('veriphy.core._errors'), layer_of('veriphy.script')
        (1, -1, None)
        >>> layer_of('veriphy.packs.core.claims'), layer_of('veriphy.packs.math.script._lie')
        (2, 0)
    """
    if module in FACADES:
        return None
    parts = module.split('.')
    if parts[1:2] == ['core']:
        return CORE
    if parts[1:2] == ['packs']:
        return LAYERS.get(parts[PACK_LAYER], 0) if len(parts) > PACK_LAYER else 0
    return LAYERS.get(parts[1]) if len(parts) > 1 else None


def module_name(path: Path) -> str:
    """Return the dotted name of a source file."""
    parts = list(path.relative_to(SRC).with_suffix('').parts)
    if parts[-1] == '__init__':
        parts.pop()
    return '.'.join(parts)


def imports(path: Path) -> list[str]:
    """Return the `veriphy` modules a source file imports, wherever the import statement sits."""
    found = []
    for node in ast.walk(ast.parse(path.read_text())):
        if isinstance(node, ast.Import):
            found += [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            found.append(node.module)
    return [name for name in found if name == 'veriphy' or name.startswith('veriphy.')]


def violations(root: Path) -> list[str]:
    """Return every import, under `root`, of a layer above the importing module's own."""
    found = []
    for path in sorted(root.rglob('*.py')):
        module = module_name(path)
        own = layer_of(module)
        if own is None:
            continue
        for imported in imports(path):
            theirs = layer_of(imported)
            if theirs is not None and theirs > own:
                found.append(f'{module} (layer {own}) imports {imported} (layer {theirs})')
    return found


def test_no_module_imports_a_higher_layer() -> None:
    """Find no import of a higher layer in the package."""
    assert violations(SRC / 'veriphy') == []


def test_an_upward_import_is_named(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Name the module, the import and both layers when a step module imports the claims layer."""
    package = tmp_path / 'veriphy' / 'steps'
    package.mkdir(parents=True)
    (package / '_bad.py').write_text('from veriphy.claims import load_graph\n')
    monkeypatch.setattr(f'{__name__}.SRC', tmp_path)
    assert violations(tmp_path / 'veriphy') == ['veriphy.steps._bad (layer 1) imports veriphy.claims (layer 2)']


def test_the_sage_session_needs_no_command_line_library() -> None:
    """Import what the Sage session imports without click, which Sage's own Python may lack."""
    modules = 'veriphy, veriphy.steps, veriphy.primitives, veriphy.packs.math.primitives'
    code = f'import sys, {modules}; print("click" in sys.modules)'
    done, out, err = run_process([sys.executable, '-c', code], SRC.parent)
    assert (done, out.strip()) == (0, 'False'), err
