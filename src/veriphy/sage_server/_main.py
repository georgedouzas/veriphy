"""Serve the daemon protocol on stdin and stdout."""

import importlib
import json
import sys

NOT_UNDER_SAGE = (
    "veriphy's daemon must run under SageMath: `sage -python -m veriphy.sage_server` "
    '(install it into Sage with `sage -pip install veriphy`)\n'
)
SAGE_UNAVAILABLE = 2


def main() -> None:
    """Answer one JSON request per stdin line with one JSON response per stdout line, until stdin closes."""
    try:
        oracle = importlib.import_module('veriphy.oracle')
    except ModuleNotFoundError as exc:
        if not (exc.name or '').startswith('sage'):
            raise
        sys.stderr.write(NOT_UNDER_SAGE)
        raise SystemExit(SAGE_UNAVAILABLE) from exc
    for line in sys.stdin:
        stripped = line.strip()
        if stripped:
            sys.stdout.write(json.dumps(oracle.answer_request(stripped)) + '\n')
            sys.stdout.flush()
