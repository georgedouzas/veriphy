"""Test structure constants, invariant forms, Casimirs and the Lean facts emitted for them."""

from collections.abc import Callable

import pytest
from sage.all import QQ, ZZ, QuadraticField, identity_matrix, matrix

from veriphy.core import CertificateError
from veriphy.toolkit import (
    Lean,
    bracket_relations,
    cartan_matrix,
    casimir,
    commutation_facts,
    det_certificate,
    jacobi_certificate,
    killing_form,
    positive_roots,
    smul_combination,
    structure_constants,
    trace_form,
    weyl_group_order,
)

E = matrix(QQ, [[0, 1], [0, 0]])
F = matrix(QQ, [[0, 0], [1, 0]])
H = matrix(QQ, [[1, 0], [0, -1]])
SL2 = [E, F, H]


def _su3() -> list:
    """Return a basis of su(3) with rational structure constants, over ℚ(i)."""
    field = QuadraticField(-1, 'i')
    i = field.gen()

    def unit(a: int, b: int) -> matrix:
        m = matrix(field, 3, 3)
        m[a, b] = 1
        return m

    return [
        i * (unit(0, 0) - unit(1, 1)),
        i * (unit(1, 1) - unit(2, 2)),
        unit(0, 1) - unit(1, 0),
        unit(0, 2) - unit(2, 0),
        unit(1, 2) - unit(2, 1),
        i * (unit(0, 1) + unit(1, 0)),
        i * (unit(0, 2) + unit(2, 0)),
        i * (unit(1, 2) + unit(2, 1)),
    ]


def test_structure_constants_reproduce_every_bracket() -> None:
    """Rebuild each bracket of 𝔰𝔩₂ and su(3) from the structure constants."""
    for basis in (SL2, _su3()):
        table = structure_constants(basis)
        for i, a in enumerate(basis):
            for j, b in enumerate(basis):
                rebuilt = sum((c * m for c, m in zip(table[i][j], basis, strict=True)), 0 * a)
                assert rebuilt == a * b - b * a


def test_open_and_dependent_bases_are_refused() -> None:
    """Name the first pair whose bracket leaves the span, and refuse a dependent basis."""
    with pytest.raises(CertificateError, match='⁅e0, e1⁆'):
        structure_constants([E, F])
    with pytest.raises(CertificateError, match='dependent'):
        structure_constants([E, 2 * E])


def test_forms_and_casimir() -> None:
    """The Killing form of 𝔰𝔩₂ is four times the trace form; the Casimirs are scalars that commute."""
    assert killing_form(structure_constants(SL2)) == 4 * trace_form(SL2)
    assert casimir(SL2) == QQ(3) / 8 * identity_matrix(QQ, 2)
    assert casimir(SL2, trace_form(SL2)) == QQ(3) / 2 * identity_matrix(QQ, 2)
    su3 = _su3()
    c = casimir(su3, trace_form(su3))
    assert all(c * m == m * c for m in su3)


def test_degenerate_form_is_refused() -> None:
    """The Killing form of a solvable algebra is degenerate: no Casimir for it."""
    with pytest.raises(CertificateError, match='degenerate'):
        casimir([E, H])


def test_smul_combination_renders_signs_and_rationals() -> None:
    """Leave out zeros and unit coefficients, write subtraction, and type rational coefficients."""
    assert smul_combination([1, -1, 0], ['a', 'b', 'c']) == 'a - b'
    assert smul_combination([-QQ(3) / 2], ['a']) == '-(3 / 2 : ℚ) • a'


def test_relations_unfold_only_the_names_they_use() -> None:
    """An entrywise relation unfolds the matrices it mentions, not the whole basis."""
    proof = str(bracket_relations(SL2, ['e', 'f', 'h'], pairs=[(2, 0)], entrywise_limit=2))
    assert 'unfold h e\n' in proof


def test_non_rational_constants_are_refused() -> None:
    """A basis with irrational structure constants (Gell-Mann's λ₈ direction) cannot be stated with rationals."""
    table = [[[QQ(0)], [QQ(0)]], [[QQ(0)], [QQ(0)]]]
    table[0][1][0] = QuadraticField(3, 's').gen()
    with pytest.raises(CertificateError, match='not rational'):
        jacobi_certificate(table)


def test_lie_facts_parse_in_lean(lean_parses: Callable[[list[Lean]], str]) -> None:
    """The emitted facts parse as Lean tactics."""
    facts = [
        bracket_relations(SL2, ['e', 'f', 'h']),
        bracket_relations(SL2, ['e', 'f', 'h'], entrywise_limit=2),
        commutation_facts('C', ['e', 'f', 'h'], size=2),
        jacobi_certificate(structure_constants(SL2)),
    ]
    assert lean_parses(facts) == ''


def test_root_data_matches_the_classification() -> None:
    """Determinants, Weyl group orders and root counts of the exceptional types."""
    for name, det, order, roots in [('E8', 1, 696729600, 120), ('F4', 1, 1152, 24), ('G2', 1, 12, 6)]:
        assert cartan_matrix(name).det() == det
        assert weyl_group_order(name) == order
        assert len(positive_roots(name)) == roots
    assert cartan_matrix('E₈') == cartan_matrix('E 8')


def test_unknown_types_and_pivoting_are_refused() -> None:
    """Name the expected form of a type, and refuse a matrix whose leading minor vanishes."""
    with pytest.raises(CertificateError, match='Cartan type'):
        cartan_matrix('H3')
    with pytest.raises(CertificateError, match='pivoting'):
        det_certificate(matrix(ZZ, [[0, 1], [1, 0]]))
    with pytest.raises(CertificateError, match='integer'):
        det_certificate(matrix(QQ, [[QQ(1) / 2]]))
