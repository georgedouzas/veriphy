"""Test the request and response envelope."""

from collections.abc import Callable

import veriphy
from veriphy.core import JsonObject
from veriphy.oracle import answer_request


def test_answer_request_unknown_method(daemon: Callable[..., JsonObject]) -> None:
    """Report an unknown method by name and keep the request id."""
    response = daemon('nosuch')
    assert response['id'] == 7
    assert 'nosuch' in str(response['error'])


def test_answer_request_ping() -> None:
    """Report liveness, the Sage version and the veriphy version."""
    response = answer_request('{"id":1,"method":"ping"}')
    assert response['id'] == 1
    result = response['result']
    assert isinstance(result, dict)
    assert result['ok'] is True
    assert 'sage' in result
    assert result['veriphy'] == veriphy.__version__


def test_answer_request_envelope_carries_version(daemon: Callable[..., JsonObject]) -> None:
    """Carry the veriphy version on successful and failed responses alike."""
    assert daemon('ping')['veriphy'] == veriphy.__version__
    assert daemon('nosuch')['veriphy'] == veriphy.__version__


def test_answer_request_malformed_line() -> None:
    """Answer a line that is not JSON with an error instead of raising."""
    response = answer_request('not json')
    assert response['id'] is None
    assert 'JSONDecodeError' in str(response['error'])
