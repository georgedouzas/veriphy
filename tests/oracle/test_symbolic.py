"""Test the advisory symbolic methods."""

from collections.abc import Callable

from veriphy.core import JsonObject

Ok = Callable[..., JsonObject]


def test_answer_request_symbolic_check_true(ok: Ok) -> None:
    """Decide a true identity symbolically."""
    result = ok('symbolic_check', vars=['x'], lhs='(x + 1)^2', rhs='x^2 + 2*x + 1')
    assert (result['equal'], result['method'], result['advisory']) == (True, 'symbolic', True)


def test_answer_request_symbolic_check_counterexample(ok: Ok) -> None:
    """Refute a false identity with a numeric counterexample."""
    result = ok('symbolic_check', vars=['x'], lhs='x^2', rhs='x')
    assert result['equal'] is False
    counterexample = result['counterexample']
    assert isinstance(counterexample, dict)
    assert 'x' in counterexample


def test_answer_request_solve(ok: Ok) -> None:
    """Return the solutions of a linear system."""
    result = ok('solve', vars=['x', 'y'], equations=['x + y == 3', 'x - y == 1'])
    assert result['solutions'] == [{'x': '2', 'y': '1'}]


def test_answer_request_matrix_check(ok: Ok) -> None:
    """Decide a Clifford-type anticommutator identity entry by entry."""
    result = ok(
        'matrix_check',
        matrices={'A': [[0, 1], [1, 0]], 'B': [[1, 0], [0, -1]]},
        lhs='A*B + B*A',
        rhs='zero_matrix(2)',
    )
    assert result['equal'] is True
