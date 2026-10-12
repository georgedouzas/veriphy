"""Test exact sums of squares from a numeric SDP."""

import pytest
from sage.all import QQ

from veriphy.core import CertificateError
from veriphy.toolkit import create_ring, sos_decomposition

X, Y = create_ring(['x', 'y']).gens()

SOS_INPUTS = [
    X**4 - 2 * X**3 + 2 * X**2 - 2 * X + 1,
    4 * X**2 * Y**2 - 4 * X * Y + 1,
    X**2 + X + 1,
    35 * (X * Y - 1) ** 2 / 2,
    (X**2 + Y**2 - 1) ** 2 + (X - Y) ** 2 + QQ(1) / 10,
]


@pytest.mark.parametrize('p', SOS_INPUTS)
def test_sos_decomposition_is_exact(p: object) -> None:
    """Return nonnegative rational weights whose squares sum exactly to the polynomial."""
    squares = sos_decomposition(p)
    assert all(c > 0 for c, _ in squares)
    assert sum(c * q**2 for c, q in squares) == p


def test_sos_decomposition_irreducible_quartic() -> None:
    """Decompose an irreducible quartic that does not factor into squares."""
    p = X**4 + 2 * X**2 * Y**2 + Y**4 - X**2 - 2 * X * Y - Y**2 + QQ(11) / 10
    assert len(list(p.factor())) == 1
    assert sum(c * q**2 for c, q in sos_decomposition(p)) == p


def test_sos_decomposition_rejects_non_sos() -> None:
    """Report failure for the Motzkin polynomial, nonnegative but not a sum of squares."""
    with pytest.raises(CertificateError):
        sos_decomposition(X**4 * Y**2 + X**2 * Y**4 - 3 * X**2 * Y**2 + 1)


def test_sos_decomposition_reports_inexact_rounding() -> None:
    """Report failure when every Gram matrix sits on the cone's boundary with an irrational kernel."""
    with pytest.raises(CertificateError, match='rounding'):
        sos_decomposition((X**2 + Y**2 - 1) ** 2 + (X - Y) ** 2)


def test_sos_decomposition_rejects_negative() -> None:
    """Report failure for a polynomial that takes negative values."""
    with pytest.raises(CertificateError):
        sos_decomposition(X**2 - 1)


def test_sos_decomposition_zero() -> None:
    """Return the empty decomposition for zero."""
    assert sos_decomposition(X - X) == []
