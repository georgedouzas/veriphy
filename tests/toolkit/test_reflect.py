"""Test the reflective-certificate emitters."""

import pytest
from sage.all import ZZ, matrix

from veriphy.core import CertificateError
from veriphy.toolkit import matrix_goal_proof, packed_product_certificate, prime_certificate


def test_matrix_goal_proof_switches_on_size_and_carrier() -> None:
    """Prove small or non-decidable goals entrywise, large integer and rational ones by a checker."""
    assert str(matrix_goal_proof('mul', 8, 'ℚ')).startswith('ext i j')
    assert str(matrix_goal_proof('bracket', 9, 'ℚ')) == 'exact VeriphyCheck.bracket_eq_of_check (by decide +kernel)'
    assert str(matrix_goal_proof('mul', 40, 'ℂ')).startswith('ext i j')
    with pytest.raises(CertificateError, match='unknown matrix goal kind'):
        matrix_goal_proof('det', 9, 'ℤ')


def test_packed_certificate_refuses_a_wrong_product() -> None:
    """Refuse to emit a certificate Sage already knows to be false."""
    a = matrix(ZZ, [[1, 2], [3, 4]])
    with pytest.raises(CertificateError, match='claimed product is wrong'):
        packed_product_certificate(a, a, a)


def test_prime_certificate_refuses_composites() -> None:
    """Refuse a composite number."""
    with pytest.raises(CertificateError, match='not prime'):
        prime_certificate(91)
