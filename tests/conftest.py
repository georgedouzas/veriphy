"""Provide the fixtures shared by the test suite."""

import json
from collections.abc import Callable

import pytest

from veriphy.core import JsonObject
from veriphy.oracle import answer_request

Daemon = Callable[..., JsonObject]


@pytest.fixture
def daemon() -> Daemon:
    """Return a function that sends one request through the protocol and returns the response."""

    def send(method: str, **params: object) -> JsonObject:
        """Send `method` with `params` and return the response object."""
        return answer_request(json.dumps({'id': 7, 'method': method, 'params': params}))

    return send


@pytest.fixture
def ok(daemon: Daemon) -> Daemon:
    """Return a function that sends a request and returns its result, failing the test on an error response."""

    def send(method: str, **params: object) -> JsonObject:
        """Return the result of a request that must succeed."""
        response = daemon(method, **params)
        assert 'error' not in response, response['error']
        result = response['result']
        assert isinstance(result, dict)
        return result

    return send


@pytest.fixture
def err(daemon: Daemon) -> Callable[..., str]:
    """Return a function that sends a request and returns its error text, failing the test on success."""

    def send(method: str, **params: object) -> str:
        """Return the error text of a request that must fail."""
        response = daemon(method, **params)
        assert 'error' in response, response.get('result')
        return str(response['error'])

    return send
