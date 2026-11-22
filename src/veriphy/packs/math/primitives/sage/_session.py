"""Run Sage's methods: one call per process for Veriphy's primitives, or a session for Lean while it compiles a file.

`python -m veriphy.packs.math.primitives.sage call <method> <input.json> <out.json>` answers one call, writing its
result as JSON. `… run <module:function> <input.json> <out.json>` runs a pack's own function under Sage the same way:
a subfield of mathematics keeps its code in its own package and runs it here, with PARI, GAP and Sage's libraries.
`… version` prints Sage's version. With no arguments it reads one JSON-RPC 2.0 request per stdin line and answers each
on stdout until stdin closes: Lean keeps one such session per file it compiles, so a file with many calls starts Sage
once.
"""

import importlib
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from types import ModuleType

NOT_UNDER_SAGE = (
    "veriphy's Sage methods must run under SageMath: `sage -python -m veriphy.packs.math.primitives.sage` "
    '(install it into Sage with `sage -pip install veriphy`)\n'
)
SAGE_UNAVAILABLE = 2
FAILED = 1
USAGE = (
    'usage: python -m veriphy.packs.math.primitives.sage '
    '[call <method> <input.json> <out.json> | run <module:function> <input.json> <out.json> | version]\n'
)


def _methods() -> ModuleType:
    """Import the methods, which import Sage, or exit saying that they need SageMath."""
    try:
        return importlib.import_module('veriphy.packs.math.primitives.sage.methods')
    except ModuleNotFoundError as exc:
        if not (exc.name or '').startswith('sage'):
            raise
        sys.stderr.write(NOT_UNDER_SAGE)
        raise SystemExit(SAGE_UNAVAILABLE) from exc


def _call(method: str, source: Path, target: Path) -> None:
    """Answer one call: read its parameters, write its result, or exit with status 1 and the error."""
    request = {'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': json.loads(source.read_text())}
    response = _methods().answer_request(json.dumps(request))
    error = response.get('error')
    if isinstance(error, dict):
        sys.stderr.write(f"{error.get('message')}\n")
        raise SystemExit(FAILED)
    target.write_text(json.dumps(response['result']))


def _run(function: str, source: Path, target: Path) -> None:
    """Run a pack's function under Sage on the input, writing its result, or exit with status 1 and the error."""
    _methods()
    module, _, name = function.partition(':')
    try:
        result = getattr(importlib.import_module(module), name)(json.loads(source.read_text()))
    except (ImportError, AttributeError) as exc:
        sys.stderr.write(f"no function '{function}': {exc}\n")
        raise SystemExit(FAILED) from exc
    target.write_text(json.dumps(result))


def main(argv: Sequence[str] | None = None) -> None:
    """Answer one call, print Sage's version, or serve a session on stdin and stdout.

    Args:
        argv: The arguments, `sys.argv[1:]` when `None`.

    Raises:
        SystemExit: With status 2 on bad usage or without SageMath, and 1 when a call fails.
    """
    arguments = list(sys.argv[1:] if argv is None else argv)
    match arguments:
        case ['call', method, source, target]:
            _call(method, Path(source), Path(target))
            return
        case ['run', function, source, target]:
            _run(function, Path(source), Path(target))
            return
    if arguments == ['version']:
        _methods()
        sys.stdout.write(f"SageMath version {importlib.import_module('sage.version').version}\n")
        return
    if arguments:
        sys.stderr.write(USAGE)
        raise SystemExit(SAGE_UNAVAILABLE)
    methods = _methods()
    for line in sys.stdin:
        stripped = line.strip()
        if stripped:
            sys.stdout.write(json.dumps(methods.answer_request(stripped)) + '\n')
            sys.stdout.flush()
