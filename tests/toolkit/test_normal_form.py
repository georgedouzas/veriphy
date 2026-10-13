"""Test Smith and Jordan certificates and matrix exponentials."""

from collections.abc import Callable

import pytest
from sage.all import QQ, ZZ, matrix

from veriphy.core import CertificateError
from veriphy.toolkit import (
    Lean,
    diagonalizable_exponential,
    jordan_certificate,
    nilpotency_index,
    nilpotent_exponential,
    smith_certificate,
)


def test_smith_form_and_unimodular_transforms() -> None:
    """U A V = D with D the invariant factors, and U, V of determinant ±1."""
    a = matrix(ZZ, [[2, 4, 4], [-6, 6, 12], [10, -4, -16]])
    d, u, v, _ = smith_certificate(a)
    assert u * a * v == d
    assert d.diagonal() == [2, 6, 12]
    assert abs(u.det()) == abs(v.det()) == 1
    with pytest.raises(CertificateError, match='square integer'):
        smith_certificate(matrix(QQ, [[QQ(1) / 2]]))


def test_jordan_form_and_refusal() -> None:
    """A P = P J with a nontrivial block; irrational eigenvalues are refused."""
    a = matrix(QQ, [[5, 4, 2, 1], [0, 1, -1, -1], [-1, -1, 3, 0], [1, 1, -1, 2]])
    j, p, _ = jordan_certificate(a)
    assert a * p == p * j
    assert any(j[i, i + 1] != 0 for i in range(3))
    with pytest.raises(CertificateError, match='not all rational'):
        jordan_certificate(matrix(QQ, [[0, 2], [1, 0]]))


def test_exponentials() -> None:
    """The nilpotent series stops at the index; a non-diagonalizable matrix is refused."""
    n = matrix(QQ, [[0, 1, 2], [0, 0, 3], [0, 0, 0]])
    assert nilpotency_index(n) == 3
    assert nilpotency_index(matrix(QQ, [[1]])) is None
    e, _ = nilpotent_exponential(n)
    assert e == 1 + n + n * n / 2
    with pytest.raises(CertificateError, match='not diagonalizable'):
        diagonalizable_exponential(matrix(QQ, [[1, 1], [0, 1]]))
    with pytest.raises(CertificateError, match='not nilpotent'):
        nilpotent_exponential(matrix(QQ, [[1, 1], [0, 1]]))


def test_normal_form_proofs_parse_in_lean(lean_parses: Callable[[list[Lean]], str]) -> None:
    """The certificates and exponential proofs parse as Lean tactics."""
    proofs = [
        smith_certificate(matrix(ZZ, [[2, 4], [6, 8]]))[3],
        jordan_certificate(matrix(QQ, [[2, 1], [0, 2]]))[2],
        nilpotent_exponential(matrix(QQ, [[0, 1], [0, 0]]))[1],
        diagonalizable_exponential(matrix(QQ, [[0, 1], [1, 0]]), 'φ')[1],
    ]
    assert lean_parses(proofs) == ''
