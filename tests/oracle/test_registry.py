"""Test parameter validation and dispatch of registered methods."""

from collections.abc import Callable

from veriphy.core import JsonObject


def test_answer_request_missing_parameter(err: Callable[..., str], ok: Callable[..., JsonObject]) -> None:
    """Name the missing parameter, prefixed by the method, and keep serving afterwards."""
    error = err('run_script')
    assert error.startswith('run_script: ')
    assert "'script'" in error
    assert ok('run_script', script='results = 1')['results'] == '1'


def test_answer_request_bad_integer(err: Callable[..., str]) -> None:
    """Name a parameter that must be an integer."""
    assert "'timeout_s'" in err('run_script', script='x = 1', timeout_s='soon')


def test_answer_request_removed_certificate_methods(err: Callable[..., str]) -> None:
    """Answer the removed certificate methods as unknown."""
    for method in ('factor', 'sos', 'roots', 'lincomb', 'farkas', 'exists', 'sum', 'certify'):
        assert f"unknown method '{method}'" in err(method)
