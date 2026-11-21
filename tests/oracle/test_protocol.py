"""Test the Sage session's messages: JSON-RPC 2.0 requests and responses only."""

from collections.abc import Callable

import veriphy
from veriphy.core import JsonObject
from veriphy.packs.math.primitives.sage.methods import answer_request


def test_unknown_method(sage: Callable[..., JsonObject]) -> None:
    """Answer an unknown method with JSON-RPC's method-not-found error, naming it and keeping the request id."""
    response = sage('nosuch')
    assert (response['jsonrpc'], response['id']) == ('2.0', 7)
    error = response['error']
    assert isinstance(error, dict)
    assert error['code'] == -32601
    assert 'nosuch' in str(error['message'])


def test_ping() -> None:
    """Report liveness, the Sage version and the veriphy version, as a JSON-RPC 2.0 result."""
    response = answer_request('{"jsonrpc": "2.0", "id": 1, "method": "ping"}')
    assert (response['jsonrpc'], response['id']) == ('2.0', 1)
    result = response['result']
    assert isinstance(result, dict)
    assert result['ok'] is True
    assert 'sage' in result
    assert result['veriphy'] == veriphy.__version__


def test_malformed_line() -> None:
    """Answer a line that is not JSON with an error instead of raising."""
    response = answer_request('not json')
    assert response['id'] is None
    error = response['error']
    assert isinstance(error, dict)
    assert (error['code'], 'JSONDecodeError' in str(error['message'])) == (-32700, True)


def test_request_without_jsonrpc_is_invalid() -> None:
    """Answer a request without `"jsonrpc": "2.0"` with JSON-RPC's invalid-request error."""
    error = answer_request('{"id": 1, "method": "ping"}')['error']
    assert isinstance(error, dict)
    assert error['code'] == -32600
