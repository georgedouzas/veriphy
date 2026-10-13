"""Test Nullstellensatz, radical and Positivstellensatz certificates."""

from collections.abc import Callable

import pytest

from veriphy.core import CertificateError
from veriphy.toolkit import (
    Lean,
    nullstellensatz_proof,
    positivstellensatz_proof,
    radical_proof,
    read_problem,
)


def _problem(hyps: list[dict[str, str]], goal: dict[str, str] | None = None, carrier: str = 'ℝ') -> object:
    """Return a problem over `x`, `y` with the given hypotheses and goal."""
    return read_problem(
        {
            'vars': ['x0', 'x1'],
            'atoms': ['x', 'y'],
            'carrier': carrier,
            'hyps': hyps,
            'goal': goal or {'kind': 'false'},
        },
    )


INFEASIBLE = _problem(
    [
        {'name': 'h1', 'rel': 'lt', 'poly': '(x0^2 + x1^2) - (1)', 'text': 'x ^ 2 + y ^ 2 < 1'},
        {'name': 'h2', 'rel': 'le', 'poly': '(2) - (x0 + x1)', 'text': 'x + y ≥ 2'},
    ],
)
NO_ZERO = _problem(
    [
        {'name': 'hxy', 'rel': 'eq', 'poly': '(x0 * x1) - (1)', 'text': 'x * y = 1'},
        {'name': 'hx', 'rel': 'eq', 'poly': '(x0) - (0)', 'text': 'x = 0'},
    ],
    carrier='ℚ',
)
RADICAL = _problem(
    [{'name': 'h', 'rel': 'eq', 'poly': '(x0^2) - (0)', 'text': 'x ^ 2 = 0'}],
    {
        'kind': 'rel',
        'rel': 'eq',
        'poly': '(x0) - (0)',
        'lhs': 'x',
        'rhs': '0',
        'lhs_poly': 'x0',
        'rhs_poly': '0',
        'text': 'x = 0',
    },
)


def test_positivstellensatz_uses_a_product_and_a_square() -> None:
    """The disc inside x + y ≥ 2 is refuted with (x + y - 2)² and (x - y)²."""
    proof = str(positivstellensatz_proof(INFEASIBLE))
    assert '< 0' in proof
    assert 'mul_nonneg (sub_nonneg.mpr h2) (sub_nonneg.mpr h2)' in proof
    assert 'sq_nonneg (x - y)' in proof


def test_consistent_systems_are_refused() -> None:
    """A feasible system has no certificate of any kind."""
    feasible = _problem([{'name': 'h', 'rel': 'le', 'poly': '(x0^2) - (1)', 'text': 'x ^ 2 ≤ 1'}])
    with pytest.raises(CertificateError, match='Positivstellensatz'):
        positivstellensatz_proof(feasible)
    with pytest.raises(CertificateError, match='common zero'):
        nullstellensatz_proof(_problem([{'name': 'h', 'rel': 'eq', 'poly': '(x0) - (1)', 'text': 'x = 1'}]))


def test_nullstellensatz_and_radical() -> None:
    """1 = y·x - (x·y - 1); x² = 0 gives x = 0 through the second power."""
    assert '(1 : ℚ) = 0' in str(nullstellensatz_proof(NO_ZERO))
    proof = str(radical_proof(RADICAL))
    assert '((x) - (0)) ^ 2 = 0' in proof
    assert 'pow_eq_zero_iff (n := 2)' in proof


def test_certificates_parse_in_lean(lean_parses: Callable[[list[Lean]], str]) -> None:
    """The three certificates parse as Lean tactics."""
    proofs = [positivstellensatz_proof(INFEASIBLE), nullstellensatz_proof(NO_ZERO), radical_proof(RADICAL)]
    assert lean_parses(proofs) == ''
