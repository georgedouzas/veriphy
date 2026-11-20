"""The step command: `python -m veriphy <step>`, and `records` to list and show what the steps recorded."""

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from veriphy.core import RecordError, RecordStore, find_workspace_root, read_record
from veriphy.steps._graph import REASON, REPORT, SUFFIXES, VALIDATE
from veriphy.steps._lean import ELABORATE, LEVEL
from veriphy.steps._runner import USAGE_EXIT, Params, Result, Step, exit_code, run_step

STEPS: dict[str, Step] = {step.name: step for step in (ELABORATE, LEVEL, VALIDATE, REASON, REPORT)}


def _parser() -> argparse.ArgumentParser:
    """Return the parser: one subcommand per step, and `records`."""
    parser = argparse.ArgumentParser(prog='python -m veriphy', description='Run a Veriphy step and record it.')
    parser.add_argument('--root', type=Path, default=None, help='the workspace root (found by default)')
    commands = parser.add_subparsers(dest='command', required=True)
    shared = argparse.ArgumentParser(add_help=False)
    shared.add_argument('--json', action='store_true', help='print the record as JSON, and nothing else')
    shared.add_argument('--rerun', action='store_true', help='run even when a final record of the inputs exists')
    elaborate = commands.add_parser('elaborate', parents=[shared], help='Lean checks a file, with each axiom set')
    elaborate.add_argument('file')
    level = commands.add_parser('level', parents=[shared], help='the levels of a module, from #veriphy_levels')
    level.add_argument('module')
    level.add_argument('--prefix', action='append', dest='prefixes', help='a name prefix (default: the module)')
    commands.add_parser('validate', parents=[shared], help='the graph against its shapes')
    commands.add_parser('reason', parents=[shared], help='graph reasoning, checked by oo-horn')
    report = commands.add_parser('report', parents=[shared], help='the verification appendix of a source')
    report.add_argument('source')
    report.add_argument('--format', choices=list(SUFFIXES), default='markdown')
    records = commands.add_parser('records', help='list the records, or show one by its digest')
    records.add_argument('digest', nargs='?', help='a digest, or its first characters')
    records.add_argument('--step', help='only this step')
    return parser


def _params(args: argparse.Namespace) -> Params:
    """Return a step's parameters from the parsed arguments."""
    names = ('file', 'module', 'prefixes', 'source', 'format')
    return {name: getattr(args, name) for name in names if getattr(args, name, None) is not None}


def _print(result: Result, as_json: bool) -> None:
    """Print a step's record, or its status and path."""
    if as_json:
        sys.stdout.write(json.dumps(result.record.to_json(), indent=2, sort_keys=True, ensure_ascii=False) + '\n')
        return
    how = ' (replayed)' if result.replayed else ' (unchanged)' if result.changed is False else ''
    changed = '\nthe result differs from the earlier record of the same inputs' if result.changed else ''
    sys.stdout.write(f'{result.record.step}: {result.record.status}{how}\n{result.path}{changed}\n')


def _records(root: Path, digest: str | None, step: str | None) -> None:
    """List the records, or show the one a digest names."""
    paths = RecordStore(root).all(step)
    if digest is None:
        for path in paths:
            record = read_record(path)
            sys.stdout.write(f'{record.step}\t{record.status}\t{path.stem}\n')
        return
    matches = [path for path in paths if path.stem.startswith(digest)]
    if len(matches) != 1:
        sys.stderr.write(f"{len(matches)} records match '{digest}'\n")
        raise SystemExit(USAGE_EXIT)
    sys.stdout.write(matches[0].read_text())


def main(argv: Sequence[str] | None = None) -> None:
    """Run a step and print its record, or list and show records.

    Args:
        argv: The command-line arguments, `sys.argv[1:]` when `None`.

    Raises:
        SystemExit: With status 1 when the step refused, found a counterexample or failed, 2 on bad usage and 3 when
            its result is unchecked.
    """
    args = _parser().parse_args(list(sys.argv[1:] if argv is None else argv))
    root = find_workspace_root(args.root)
    if args.command == 'records':
        _records(root, args.digest, args.step)
        return
    try:
        result = run_step(STEPS[args.command], root, _params(args), rerun=args.rerun)
    except (RecordError, FileNotFoundError, KeyError, ValueError) as exc:
        sys.stderr.write(f'{args.command}: {exc}\n')
        raise SystemExit(USAGE_EXIT) from exc
    _print(result, args.json)
    code = exit_code(result.record.status)
    if code:
        raise SystemExit(code)
