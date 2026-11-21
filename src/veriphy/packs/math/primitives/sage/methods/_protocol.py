"""Answer one request line of the daemon protocol."""

import json

from sage.all import version

from veriphy.core import JsonObject, JsonValue, Method, MethodError
from veriphy.core._version import __version__
from veriphy.packs.math.primitives.sage.methods._meaning import MEANING_METHODS
from veriphy.packs.math.primitives.sage.methods._registry import _register_method
from veriphy.packs.math.primitives.sage.methods._scripts import SCRIPT_METHODS
from veriphy.packs.math.primitives.sage.methods._symbolic import SYMBOLIC_METHODS

PROTOCOL_METHODS: dict[str, Method] = {}


@_register_method(PROTOCOL_METHODS, 'ping', raw=True)
def _ping(_params: JsonObject) -> JsonObject:
    """Return liveness and the Sage and veriphy versions."""
    return {'ok': True, 'sage': version(), 'veriphy': __version__}


METHODS: dict[str, Method] = {**PROTOCOL_METHODS, **SCRIPT_METHODS, **SYMBOLIC_METHODS, **MEANING_METHODS}


# JSON-RPC 2.0 error codes
PARSE_ERROR = -32700
METHOD_NOT_FOUND = -32601
METHOD_FAILED = -32000


def _respond(request: object, req_id: JsonValue, outcome: str, value: JsonValue, code: int) -> JsonObject:
    """Return one response: JSON-RPC 2.0 for a JSON-RPC request, else the shape of earlier releases (deprecated)."""
    if isinstance(request, dict) and request.get('jsonrpc') == '2.0':
        if outcome == 'result':
            return {'jsonrpc': '2.0', 'id': req_id, 'result': value}
        return {'jsonrpc': '2.0', 'id': req_id, 'error': {'code': code, 'message': value}}
    return {'id': req_id, outcome: value, 'veriphy': __version__}


def answer_request(line: str) -> JsonObject:
    """Answer one request line with one response object, never raising.

    A request is JSON-RPC 2.0 (`{"jsonrpc": "2.0", "id", "method", "params"}`), answered with `result` or with
    `error: {code, message}`. A request without `"jsonrpc"` is answered as earlier releases did, with `result` or an
    `error` string, until the next minor release.

    Args:
        line: The request.

    Returns:
        The response.

    Examples:
        >>> answer_request('{"jsonrpc": "2.0", "id": 1, "method": "ping"}')['result']['ok']
        True
        >>> answer_request('{"jsonrpc": "2.0", "id": 2, "method": "nosuch"}')['error']['code']
        -32601
        >>> answer_request('{"id": 3, "method": "ping"}')['result']['ok']
        True
    """
    request: object = None
    req_id: JsonValue = None
    try:
        request = json.loads(line)
        if not isinstance(request, dict):
            return _respond(request, None, 'error', 'a request must be a JSON object', PARSE_ERROR)
        req_id = request.get('id')
        name = request.get('method')
        if name not in METHODS:
            known = f"unknown method '{name}' (known: {sorted(METHODS)})"
            return _respond(request, req_id, 'error', known, METHOD_NOT_FOUND)
        return _respond(request, req_id, 'result', METHODS[name](request.get('params') or {}), 0)
    except MethodError as exc:
        return _respond(request, req_id, 'error', str(exc), METHOD_FAILED)
    except json.JSONDecodeError as exc:
        return _respond(request, req_id, 'error', f'{type(exc).__name__}: {exc}', PARSE_ERROR)
