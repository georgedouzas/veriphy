"""The primitive command: `veriphy primitive list`, `describe <primitive>` and `run <primitive> --input <file>`."""

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from veriphy.core import VeriphyError, find_workspace_root, resolve
from veriphy.primitives._registry import Registry, load_registry

USAGE_EXIT = 2
FAILED_EXIT = 1


def _parser() -> argparse.ArgumentParser:
    """Return the parser of the three subcommands."""
    parser = argparse.ArgumentParser(prog='veriphy primitive', description='Run a primitive, with no record.')
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('list', help='every primitive, with its trust class, its pack, and whether it can run here')
    describe = commands.add_parser('describe', help="a primitive's tool, pin, trust class and schemas")
    describe.add_argument('name')
    run = commands.add_parser('run', help='run a primitive on a JSON input and print its output')
    run.add_argument('name')
    run.add_argument('--input', type=Path, help='a JSON file holding the input (default: standard input)')
    return parser


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


def main(argv: Sequence[str] | None = None) -> None:
    """List, describe or run primitives.

    Args:
        argv: The command-line arguments, `sys.argv[1:]` when `None`.

    Raises:
        SystemExit: With status 1 when the primitive fails, and 2 on bad usage.
    """
    args = _parser().parse_args(list(sys.argv[1:] if argv is None else argv))
    try:
        if args.command == 'list':
            sys.stdout.write(_list())
        elif args.command == 'describe':
            sys.stdout.write(_describe(args.name))
        else:
            sys.stdout.write(_run(args.name, args.input))
    except json.JSONDecodeError as exc:
        sys.stderr.write(f'primitive: the input is not JSON: {exc}\n')
        raise SystemExit(USAGE_EXIT) from exc
    except VeriphyError as exc:
        sys.stderr.write(f'primitive: {exc}\n')
        raise SystemExit(FAILED_EXIT) from exc
