"""Answer one request line of the Sage session protocol."""

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
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
METHOD_FAILED = -32000


def _result(req_id: JsonValue, value: JsonValue) -> JsonObject:
    """Return a JSON-RPC 2.0 response carrying a result."""
    return {'jsonrpc': '2.0', 'id': req_id, 'result': value}


def _error(req_id: JsonValue, code: int, message: str) -> JsonObject:
    """Return a JSON-RPC 2.0 response carrying an error."""
    return {'jsonrpc': '2.0', 'id': req_id, 'error': {'code': code, 'message': message}}


def answer_request(line: str) -> JsonObject:
    """Answer one JSON-RPC 2.0 request line with one response object, never raising.

    A request is `{"jsonrpc": "2.0", "id", "method", "params"}`, answered with `result` or with
    `error: {code, message}`.

    Args:
        line: The request.

    Returns:
        The response.

    Examples:
        >>> answer_request('{"jsonrpc": "2.0", "id": 1, "method": "ping"}')['result']['ok']
        True
        >>> answer_request('{"jsonrpc": "2.0", "id": 2, "method": "nosuch"}')['error']['code']
        -32601
        >>> answer_request('{"id": 3, "method": "ping"}')['error']['code']
        -32600
    """
    req_id: JsonValue = None
    try:
        request = json.loads(line)
        if not isinstance(request, dict) or request.get('jsonrpc') != '2.0':
            return _error(None, INVALID_REQUEST, 'a request must be a JSON-RPC 2.0 object, with "jsonrpc": "2.0"')
        req_id = request.get('id')
        name = request.get('method')
        if name not in METHODS:
            return _error(req_id, METHOD_NOT_FOUND, f"unknown method '{name}' (known: {sorted(METHODS)})")
        return _result(req_id, METHODS[name](request.get('params') or {}))
    except MethodError as exc:
        return _error(req_id, METHOD_FAILED, str(exc))
    except json.JSONDecodeError as exc:
        return _error(None, PARSE_ERROR, f'{type(exc).__name__}: {exc}')
