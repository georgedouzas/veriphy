"""Test the exact JSON encoding of results."""

import pytest
from sage.all import QQ, PolynomialRing, RealField

from veriphy.core import EncodingError
from veriphy.oracle import encode


def test_encode_rationals_and_polynomials_exactly() -> None:
    """Encode rationals as strings and polynomials as term lists."""
    ring = PolynomialRing(QQ, 2, ['x0', 'x1'])
    x0, x1 = ring.gens()
    assert encode(QQ(1) / 3) == '1/3'
    assert encode({'m': [QQ(-3) / 2, 5]}) == {'m': ['-3/2', 5]}
    assert encode(2 * x0**2 * x1 - 1) == [{'coeff': '-1', 'exps': [0, 0]}, {'coeff': '2', 'exps': [2, 1]}]


def test_encode_rejects_floats_in_certificates() -> None:
    """Reject floats in certificate results and allow them in advisory ones."""
    with pytest.raises(EncodingError):
        encode(0.5)
    with pytest.raises(EncodingError):
        encode(RealField(53)(0.5))
    assert encode(0.5, advisory=True) == 0.5
    assert encode(RealField(53)(0.5), advisory=True) == '0.500000000000000'
