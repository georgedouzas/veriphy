"""Test the linear-algebra certificates: minors, factorisations, relations, kernels, congruences."""

import pytest
from sage.all import QQ, matrix

from veriphy.core import CertificateError
from veriphy.toolkit import (
    dependence_relation,
    independence_proof,
    intersection_dimension_proof,
    kernel_basis,
    nonlinearity_proof,
    nonzero_minor,
    rank_factorization,
    rank_proof,
    signature,
    span_coordinates,
    span_proof,
    symmetric_congruence,
)


def test_minors_and_factorisations() -> None:
    """A rank-one matrix has a 1 × 1 minor, no 2 × 2 one, and factors through one column."""
    a = matrix(QQ, [[1, 2, 3], [2, 4, 6]])
    assert nonzero_minor(a, 1) == ([0], [0])
    with pytest.raises(CertificateError, match='every 2 × 2 minor is singular'):
        nonzero_minor(a, 2)
    b, c = rank_factorization(a)
    assert b * c == a
    assert b.ncols() == 1


def test_relations_coordinates_and_kernels() -> None:
    """Relations, coordinates and kernel bases agree with their definitions."""
    assert dependence_relation([[1, 2], [2, 4]]) == [2, -1]
    with pytest.raises(CertificateError, match='independent'):
        dependence_relation([[1, 0], [0, 1]])
    assert span_coordinates([1, 3], [[1, 1], [0, 1]]) == [1, 2]
    with pytest.raises(CertificateError, match='not in the span'):
        span_coordinates([0, 0, 1], [[1, 0, 0], [0, 1, 0]])
    basis, free = kernel_basis(matrix(QQ, [[1, 1, 1]]))
    assert free == [1, 2]
    assert all(sum(v) == 0 for v in basis)


def test_congruences_diagonalise() -> None:
    """Pᵀ S P is diagonal with the reported diagonal, also when the first pivot is zero."""
    for rows in (
        [[2, 1, 0], [1, 2, 1], [0, 1, 2]],
        [[0, 1], [1, 0]],
        [[1, 0, 0, 0], [0, -1, 0, 0], [0, 0, -1, 0], [0, 0, 0, -1]],
    ):
        s = matrix(QQ, rows)
        p, d = symmetric_congruence(s)
        assert p.det() != 0
        assert p.transpose() * s * p == matrix.diagonal(QQ, d)
    assert signature(symmetric_congruence(matrix(QQ, [[0, 1], [1, 0]]))[1]) == (1, 1, 0)


def test_emitters_refuse_false_claims() -> None:
    """Independence of a dependent family, its negation for an independent one, and unequal spans are refused."""
    with pytest.raises(CertificateError, match='dependent'):
        independence_proof([[1, 2], [2, 4]])
    with pytest.raises(CertificateError, match='independent'):
        independence_proof([[1, 0], [0, 1]], negated=True)
    with pytest.raises(CertificateError, match='not in the span'):
        span_proof([[1, 0, 0]], other=[[0, 1, 0]])
    with pytest.raises(CertificateError, match='does not span the kernel'):
        span_proof([[1, 0, 0]], kernel_of=matrix(QQ, [[1, 1, 1]]))
    with pytest.raises(CertificateError, match='must be independent'):
        intersection_dimension_proof([[1, 0], [2, 0]], [[0, 1]])
    with pytest.raises(CertificateError, match='unknown rank goal'):
        rank_proof(matrix(QQ, [[1]]), 'lt')
    with pytest.raises(CertificateError, match='vanishes at zero'):
        nonlinearity_proof(lambda x, y: x * y, 2)


def test_rank_proof_shapes() -> None:
    """A full-rank square matrix is bounded by its height; a rank-one one by a factorisation."""
    assert 'Matrix.rank_le_height' in rank_proof(matrix(QQ, [[1, 2], [3, 4]]))
    assert 'rank_le_of_factor' in rank_proof(matrix(QQ, [[1, 2, 3], [2, 4, 6]]))
