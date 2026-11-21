"""The primitive command: `veriphy primitive list`, `describe <primitive>` and `run <primitive> --input <file>`."""

import json
import sys
from collections.abc import Callable, Sequence
from pathlib import Path

import click

from veriphy.core import VeriphyError, find_workspace_root, resolve
from veriphy.core._commands import run_command
from veriphy.primitives._registry import Registry, load_registry

USAGE_EXIT = 2
FAILED_EXIT = 1


def _workspace() -> Registry:
    """Return the registry of the current workspace's packs, as its `veriphy.yaml` selects them."""
    return load_registry(resolved=resolve(find_workspace_root()))


def _list() -> str:
    """Return one line per primitive."""
    registry = _workspace()
    lines = []
    for name, primitive in sorted(registry.primitives.items()):
        missing = registry.unavailable(name)
        state = f'unavailable: {missing}' if missing else 'available'
        lines.append(f'{name}\t{primitive.trust}\t{primitive.pack}\t{state}')
    return '\n'.join(lines) + '\n'


def _describe(name: str) -> str:
    """Return a primitive's description, as JSON."""
    registry = _workspace()
    primitive = registry.get(name)
    tool = registry.tools.get(primitive.tool)
    description: dict[str, object] = {
        'name': primitive.name,
        'pack': primitive.pack,
        'trust': primitive.trust,
        'input': dict(primitive.input_schema),
        'output': dict(primitive.output_schema),
    }
    if primitive.composite:
        description |= {'parts': list(primitive.parts), 'decides': primitive.decides}
    elif primitive.function:
        description |= {'function': primitive.function, 'seed': primitive.seed}
    elif tool is not None:
        pin = None if tool.pin is None else {tool.pin.kind: tool.pin.value}
        description |= {'tool': tool.name, 'contract': tool.contract, 'pin': pin, 'seed': primitive.seed}
    return json.dumps(description, indent=2, ensure_ascii=False) + '\n'


def _run(name: str, source: Path | None) -> str:
    """Run a primitive and return its output, as JSON."""
    text = source.read_text() if source is not None else sys.stdin.read()
    inputs = json.loads(text)
    if not isinstance(inputs, dict):
        message = 'the input must be a JSON object'
        raise VeriphyError(message)
    registry = _workspace()
    try:
        output = registry.call(name, inputs)
    finally:
        registry.close()
    return json.dumps(output, indent=2, sort_keys=True, ensure_ascii=False) + '\n'


@click.group(name='primitive', help='Run a primitive by hand, with no record.')
def primitive() -> None:
    """List, describe or run primitives."""


def _guarded(write: Callable[[], str]) -> None:
    """Write what a subcommand returns, exiting with status 1 on a primitive's error and 2 on input that is not JSON."""
    try:
        sys.stdout.write(write())
    except json.JSONDecodeError as exc:
        sys.stderr.write(f'primitive: the input is not JSON: {exc}\n')
        raise SystemExit(USAGE_EXIT) from exc
    except VeriphyError as exc:
        sys.stderr.write(f'primitive: {exc}\n')
        raise SystemExit(FAILED_EXIT) from exc


@primitive.command(name='list', help='every primitive, with its trust class, its pack, and whether it can run here')
def list_primitives() -> None:
    """List the workspace's primitives."""
    _guarded(_list)


@primitive.command(help="a primitive's tool, pin, trust class and schemas")
@click.argument('name')
def describe(name: str) -> None:
    """Describe one primitive, as JSON."""
    _guarded(lambda: _describe(name))


@primitive.command(help='run a primitive on a JSON input and print its output')
@click.argument('name')
@click.option('--input', 'source', type=click.Path(path_type=Path), default=None, help='a JSON file (default: stdin)')
def run(name: str, source: Path | None) -> None:
    """Run one primitive, as JSON in and out."""
    _guarded(lambda: _run(name, source))


def main(argv: Sequence[str] | None = None) -> None:
    """List, describe or run primitives.

    Args:
        argv: The command-line arguments, `sys.argv[1:]` when `None`.
    """
    run_command(primitive, argv, 'veriphy primitive')
