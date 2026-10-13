"""Test supermatrix superalgebras, the exceptional families and the super-Jacobi certificates."""

from collections.abc import Callable

import pytest
from sage.all import QQ, FractionField, identity_matrix, matrix

from veriphy.core import CertificateError
from veriphy.toolkit import (
    Lean,
    contragredient_superalgebra,
    d21_alpha,
    g3,
    graded_commutator,
    integral_rescaling,
    parity_of,
    sparse_rows_term,
    super_casimir,
    super_jacobi_certificate,
    super_jacobi_family_certificate,
    super_jacobi_violations,
    super_relations,
    super_structure_constants,
    supertrace,
    supertrace_form,
)
from veriphy.toolkit._superalgebra import EPSILON, SL2, _kron


def _unit(i: int, j: int, n: int = 3) -> matrix:
    """Return the matrix unit `Eᵢⱼ`."""
    m = matrix(QQ, n, n)
    m[i, j] = 1
    return m


# osp(1|2) on (1|2): the even coordinate first, then the two odd ones
H = _unit(1, 1) - _unit(2, 2)
E, F = _unit(1, 2), _unit(2, 1)
QP, QM = _unit(1, 0) + _unit(0, 2), _unit(2, 0) - _unit(0, 1)
OSP = [H, E, F, QP, QM]
OSP_PARITIES = [parity_of(m, 1) for m in OSP]


def test_parities_and_supertrace() -> None:
    """Read parities from the block structure; refuse a mixed supermatrix; take supertraces."""
    assert OSP_PARITIES == [0, 0, 0, 1, 1]
    with pytest.raises(CertificateError, match='homogeneous'):
        parity_of(E + QP, 1)
    assert supertrace(identity_matrix(QQ, 3), 1) == -1


def test_osp12_brackets_and_casimir() -> None:
    """`{Q₊, Q₋} = -h`, super-Jacobi holds, and the Casimir commutes with every generator."""
    table = super_structure_constants(OSP, OSP_PARITIES)
    assert table[3][4] == [-1, 0, 0, 0, 0]
    assert graded_commutator(QP, QP, 1, 1) == 2 * E
    assert super_jacobi_violations(table, OSP_PARITIES) == []
    casimir = super_casimir(OSP, OSP_PARITIES, supertrace_form(OSP, 1))
    assert all(casimir * x == x * casimir for x in OSP)


def test_sl11_and_wrong_parity() -> None:
    """`sl(1|1)`: the odd generators anticommute to the central element; a bracket of the wrong parity is refused."""
    z, p, m = identity_matrix(QQ, 2), _unit(0, 1, 2), _unit(1, 0, 2)
    assert super_structure_constants([z, p, m], [0, 1, 1])[1][2] == [1, 0, 0]
    # in gl(1|1), the even N = E₀₀ labelled odd: {N, P} = P is in the span but odd
    with pytest.raises(CertificateError, match='wrong parity'):
        super_structure_constants([z, _unit(0, 0, 2), p, m], [0, 1, 1, 1])


def test_d21_alpha_is_a_family_and_other_coefficients_fail() -> None:
    """D(2,1;α) satisfies super-Jacobi for symbolic α; coefficients off the plane k₁ + k₂ + k₃ = 0 do not."""
    alpha = FractionField(QQ['a']).gen()
    table, parities = d21_alpha(alpha)
    assert len(table) == 17
    assert super_jacobi_violations(table, parities) == []
    one = identity_matrix(QQ, 2)
    even = [_kron(s, one, one) for s in SL2] + [_kron(one, s, one) for s in SL2] + [_kron(one, one, s) for s in SL2]
    broken, _ = contragredient_superalgebra(
        even,
        [0] * 3 + [1] * 3 + [2] * 3,
        _kron(EPSILON, EPSILON, EPSILON),
        [1, 1, 1],
    )
    assert super_jacobi_violations(broken, parities)


def test_g3_rescales_to_integers() -> None:
    """G(3) is 31-dimensional; a rescaling of the basis makes its constants integers and keeps super-Jacobi."""
    table, parities = g3()
    assert (len(table), sum(parities)) == (31, 14)
    rescaled, (mu, lam) = integral_rescaling(table, parities)
    assert all(QQ(c).denominator() == 1 for plane in rescaled for row in plane for c in row)
    assert mu >= 1
    assert lam >= 1
    assert super_jacobi_violations(rescaled, parities) == []


def test_certificates_refuse_violations() -> None:
    """A table that breaks super-Jacobi gets no certificate."""
    table = super_structure_constants(OSP, OSP_PARITIES)
    table[3][4] = [1, 0, 0, 0, 0]
    with pytest.raises(CertificateError, match='super-Jacobi fails'):
        super_jacobi_certificate(table, OSP_PARITIES)


def test_superalgebra_facts_parse_in_lean(lean_parses: Callable[[list[Lean]], str]) -> None:
    """The certificates and graded relations parse as Lean tactics."""
    table = super_structure_constants(OSP, OSP_PARITIES)
    t0, parities = d21_alpha(QQ(0))
    t1p, _ = d21_alpha(QQ(1))
    t1 = [[[t1p[i][j][k] - t0[i][j][k] for k in range(17)] for j in range(17)] for i in range(17)]
    facts = [
        super_jacobi_certificate(table, OSP_PARITIES),
        super_jacobi_family_certificate(t0, t1, parities),
        super_relations(OSP, OSP_PARITIES, ['h', 'e', 'f', 'qp', 'qm']),
    ]
    first_row = '[[], [(1, 2)], [(2, -2)], [(3, 1)], [(4, -1)]]'
    assert sparse_rows_term(table).startswith(f'(fun (i j : Fin 5) => ((([{first_row}, ')
    assert lean_parses(facts) == ''
