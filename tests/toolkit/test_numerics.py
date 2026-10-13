"""Test certified bounds, root isolation and eigenvalue certificates."""

from collections.abc import Callable

import pytest
from sage.all import QQ, matrix, polygen

from veriphy.core import CertificateError
from veriphy.toolkit import (
    Lean,
    bound_proof,
    characteristic_polynomial,
    eigenvalue_proof,
    isolate_roots,
    root_proof,
)


def test_bounds_prefer_mathlib_lemmas_then_series() -> None:
    """π and e use mathlib's decimals; exp(1/2) needs the series; false or unsupported bounds are refused."""
    assert 'Real.pi_gt_d6' in str(bound_proof('pi', 0, QQ(314159) / 100000, upper=False))
    assert 'Real.exp_bound' in str(bound_proof('exp', QQ(1) / 2, QQ(16488) / 10000))
    with pytest.raises(CertificateError, match='fails or is too tight'):
        bound_proof('exp', 1, QQ(27182) / 10000)
    with pytest.raises(CertificateError, match='for gamma'):
        bound_proof('gamma', QQ(1) / 3, 3)
    with pytest.raises(CertificateError, match='0 < x < 2'):
        bound_proof('log', 3, 2)


def test_isolated_roots_have_one_sign_change_and_no_critical_point() -> None:
    """Each interval of x³ - 2x - 1 holds exactly one root."""
    x = polygen(QQ, 'x')
    p = x**3 - 2 * x - 1
    intervals = isolate_roots(p)
    assert len(intervals) == 3
    assert all(p(a) * p(b) < 0 for a, b in intervals)
    with pytest.raises(CertificateError, match='opposite signs'):
        root_proof('x ^ 3 - 2 * x - 1', 2, 3, p)


def test_eigenvalues_through_the_characteristic_polynomial() -> None:
    """The discrete Laplacian's characteristic polynomial; a non-3×3 matrix is refused."""
    m = matrix(QQ, [[2, -1, 0], [-1, 2, -1], [0, -1, 2]])
    assert characteristic_polynomial(m) == polygen(QQ, 'x') ** 3 - 6 * polygen(QQ, 'x') ** 2 + 10 * polygen(QQ, 'x') - 4
    with pytest.raises(CertificateError, match='3 by 3'):
        eigenvalue_proof(matrix(QQ, [[1]]), '!![1]', 0, 2)


def test_numerics_proofs_parse_in_lean(lean_parses: Callable[[list[Lean]], str]) -> None:
    """The proofs parse as Lean tactics."""
    x = polygen(QQ, 'x')
    proofs = [
        bound_proof('log', QQ(3) / 2, QQ(4055) / 10000),
        root_proof('x ^ 3 - 2 * x - 1', QQ(3) / 2, 3, x**3 - 2 * x - 1),
        eigenvalue_proof(matrix(QQ, [[2, -1, 0], [-1, 2, -1], [0, -1, 2]]), '!![2, -1, 0; -1, 2, -1; 0, -1, 2]', 3, 4),
    ]
    assert lean_parses(proofs) == ''
