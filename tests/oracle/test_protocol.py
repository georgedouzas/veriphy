"""Test the daemon's messages: JSON-RPC 2.0, and the format of earlier releases it still answers."""

from collections.abc import Callable

import veriphy
from veriphy.core import JsonObject
from veriphy.packs.math.primitives.sage.methods import answer_request


def test_unknown_method(daemon: Callable[..., JsonObject]) -> None:
    """Answer an unknown method with JSON-RPC's method-not-found error, naming it and keeping the request id."""
    response = daemon('nosuch')
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
    assert 'JSONDecodeError' in str(response['error'])


def test_earlier_format_still_answered() -> None:
    """Answer a request without `jsonrpc` as earlier releases did: an error string, the version on the envelope."""
    ok = answer_request('{"id": 1, "method": "ping"}')
    assert (ok['veriphy'], 'jsonrpc' in ok) == (veriphy.__version__, False)
    failed = answer_request('{"id": 2, "method": "nosuch"}')
    assert isinstance(failed['error'], str)
    assert "unknown method 'nosuch'" in failed['error']
