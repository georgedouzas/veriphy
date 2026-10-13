"""Test number-field rendering, generator facts and the reduction proofs."""

from collections.abc import Callable

import pytest
from sage.all import QQ, CyclotomicField, FractionField, PolynomialRing, QuadraticField, matrix

from veriphy.core import CertificateError
from veriphy.toolkit import (
    Lean,
    check_matrix_identity,
    cyclotomic_context,
    field_identity,
    field_matrix_identity,
    field_matrix_term,
    lift,
    parameter_context,
    quadratic_context,
    render_element,
    render_polynomial,
)

X = PolynomialRing(QQ, 'x').gen()


def test_rendering_in_each_field() -> None:
    """Render elements of ℚ(√3), ℚ(ζ₁₆) and ℚ(α) in their generators."""
    s = QuadraticField(3, 's').gen()
    assert render_element(1 - s / 3, quadratic_context(3)) == '-(1 / 3) * (Real.sqrt 3) + 1'
    z = CyclotomicField(16, 'z').gen()
    assert render_element(z**9, cyclotomic_context(16)) == '-ζ'
    a = FractionField(QQ['a']).gen()
    assert render_element((a + 1) / (a**2), parameter_context()) == '(α + 1) / (α ^ 2)'
    assert render_polynomial(X.parent()(0), 'ζ') == '0'


def test_lift_has_degree_below_the_field() -> None:
    """Lift a cyclotomic element to its reduced representative."""
    z = CyclotomicField(5, 'z').gen()
    assert lift(z**5) == 1
    assert lift(z**4) == -(X**3 + X**2 + X + 1)


def test_reductions_are_exact_divisions() -> None:
    """Each power fact `gᵏ = r(g)` comes with the quotient that proves it: `xᵏ - r = q · m`."""
    proof = str(field_identity(cyclotomic_context(16), max_power=17))
    assert 'show ζ ^ 9 = -ζ by linear_combination (ζ) * hΦ' in proof
    assert 'show ζ ^ 16 = 1 by linear_combination (ζ ^ 8 - 1) * hΦ' in proof


def test_generator_facts() -> None:
    """Derive Φₙ(ζ) = 0 from IsPrimitiveRoot for prime powers; ask for it otherwise; refuse a square under √."""
    assert 'Polynomial.cyclotomic_prime_pow_eq_geom_sum' in str(cyclotomic_context(9).setup)
    with pytest.raises(CertificateError, match='prime powers'):
        cyclotomic_context(12)
    assert cyclotomic_context(12, primitive=None).setup is None
    with pytest.raises(CertificateError, match='non-square'):
        quadratic_context(4)


def test_matrix_identity_is_checked_in_sage_first() -> None:
    """Show the difference of a false identity before Lean sees it."""
    s = QuadraticField(2, 's').gen()
    rotation = matrix([[s / 2, -s / 2], [s / 2, s / 2]])
    check_matrix_identity(rotation * rotation.transpose(), matrix.identity(2))
    with pytest.raises(CertificateError, match='difference'):
        check_matrix_identity(rotation * rotation, matrix.identity(2))
    assert str(field_matrix_term(rotation, quadratic_context(2))).startswith('!![(1 / 2) * (Real.sqrt 2), ')


def test_number_field_proofs_parse_in_lean(lean_parses: Callable[[list[Lean]], str]) -> None:
    """The proofs parse as Lean tactics in every field."""
    proofs = [
        field_identity(quadratic_context(2), max_power=4),
        field_identity(cyclotomic_context(5), max_power=8),
        field_matrix_identity(quadratic_context(2)),
        field_matrix_identity(parameter_context()),
    ]
    assert lean_parses(proofs) == ''
