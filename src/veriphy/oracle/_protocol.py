"""Answer one request line of the daemon protocol."""

import json

from sage.all import version

from veriphy.core import JsonObject, JsonValue, Method, MethodError
from veriphy.core._version import __version__
from veriphy.oracle._certificates import CERTIFICATE_METHODS
from veriphy.oracle._registry import _register_method
from veriphy.oracle._scripts import SCRIPT_METHODS
from veriphy.oracle._symbolic import SYMBOLIC_METHODS

PROTOCOL_METHODS: dict[str, Method] = {}


@_register_method(PROTOCOL_METHODS, 'ping', raw=True)
def _ping(_params: JsonObject) -> JsonObject:
    """Return liveness and the Sage and veriphy versions."""
    return {'ok': True, 'sage': version(), 'veriphy': __version__}


METHODS: dict[str, Method] = {**PROTOCOL_METHODS, **CERTIFICATE_METHODS, **SCRIPT_METHODS, **SYMBOLIC_METHODS}


def _respond(req_id: JsonValue, key: str, value: JsonValue) -> JsonObject:
    """Return one response envelope carrying the daemon's version."""
    return {'id': req_id, key: value, 'veriphy': __version__}


def answer_request(line: str) -> JsonObject:
    """Answer one JSON request line with one response object, never raising.

    Args:
        line: A JSON object with `id`, `method` and optional `params`.

    Returns:
        The response: `{"id", "result", "veriphy"}` on success, `{"id", "error", "veriphy"}` on failure.

    Examples:
        >>> answer_request('{"id": 1, "method": "ping"}')['result']['ok']
        True
        >>> answer_request('{"id": 2, "method": "nosuch"}')['error'].startswith("unknown method 'nosuch'")
        True
    """
    req_id: JsonValue = None
    try:
        req = json.loads(line)
        req_id = req.get('id')
        name = req.get('method')
        if name not in METHODS:
            return _respond(req_id, 'error', f"unknown method '{name}' (known: {sorted(METHODS)})")
        return _respond(req_id, 'result', METHODS[name](req.get('params') or {}))
    except MethodError as exc:
        return _respond(req_id, 'error', str(exc))
    except (json.JSONDecodeError, AttributeError) as exc:
        return _respond(req_id, 'error', f'{type(exc).__name__}: {exc}')
