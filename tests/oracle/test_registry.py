"""Test parameter validation of registered methods."""

from collections.abc import Callable

from veriphy.core import JsonObject


def test_answer_request_invalid_vars_names_parameter(
    err: Callable[..., str],
    ok: Callable[..., JsonObject],
) -> None:
    """Name `vars` in the error and keep serving afterwards."""
    error = err('factor', poly='x0', vars=['x0', '1y'])
    assert error.startswith('factor: ')
    assert "'vars'" in error
    assert ok('factor', poly='x0^2 - 1', vars=['x0'])['unit'] == '1'


def test_answer_request_missing_and_foreign_polynomial(err: Callable[..., str]) -> None:
    """Name `poly` when it is missing or mentions an unknown variable."""
    assert "'poly'" in err('factor', vars=['x0'])
    assert "'poly'" in err('factor', poly='x0 + y', vars=['x0'])


def test_answer_request_bad_relation(err: Callable[..., str]) -> None:
    """Name `rels` when a relation tag is not allowed."""
    assert "'rels'" in err('farkas', polys=['x0'], rels=['ne'], vars=['x0'])
