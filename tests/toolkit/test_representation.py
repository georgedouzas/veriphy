"""Test explicit representations, their decompositions, intertwiners and the facts emitted for them."""

from collections.abc import Callable

import pytest
from sage.all import QQ, block_diagonal_matrix, identity_matrix, matrix

from veriphy.core import CertificateError
from veriphy.toolkit import (
    Lean,
    adjoint_matrices,
    change_of_basis_facts,
    clebsch_gordan,
    cyclic_submodule,
    decomposition,
    defining_representation,
    eigen_projectors,
    exterior_square,
    intertwiners,
    intertwining_facts,
    projector_facts,
    representation_relations,
    restrict,
    spin_representation,
    structure_constants,
    tensor_representation,
)

SL2 = spin_representation(1)
TABLE = structure_constants(SL2)


def _is_representation(rho: list) -> bool:
    """Whether the matrices satisfy 𝔰𝔩₂'s relations in the order e, f, h."""
    e, f, h = rho
    return e * f - f * e == h and h * e - e * h == 2 * e and h * f - f * h == -2 * f


def test_spin_and_product_representations_satisfy_the_relations() -> None:
    """Spin j, products of spins and the adjoint all represent 𝔰𝔩₂."""
    for two_j in range(5):
        assert _is_representation(spin_representation(two_j))
    assert _is_representation(tensor_representation(spin_representation(2), spin_representation(1)))
    assert _is_representation(adjoint_matrices(TABLE))


def test_highest_weight_module_is_cyclic() -> None:
    """The highest weight vector e₀ ⊗ e₀ of V ⊗ V for 𝔰𝔩₃ generates Sym²V, of dimension 6."""
    rho, _ = defining_representation('A2')
    product = tensor_representation(rho, rho)
    v = [1] + [0] * 8
    basis = cyclic_submodule(product, v)
    assert basis.ncols() == 6
    assert len(restrict(product, basis)) == len(rho)


def test_exterior_square_of_the_defining_representation() -> None:
    """Λ² of 𝔰𝔩₅'s defining representation has dimension 10 and is a representation."""
    rho, labels = defining_representation('A4')
    wedge, pairs = exterior_square(rho)
    assert wedge[0].nrows() == len(pairs) == 10
    index = {label: i for i, label in enumerate(labels)}
    e, f, h = wedge[index['e1']], wedge[index['f1']], wedge[index['h1']]
    assert _is_representation([e, f, h])


def test_intertwiners_follow_schur() -> None:
    """One intertwiner (up to scale) between isomorphic irreducibles, none between different spins."""
    assert len(intertwiners(spin_representation(2), spin_representation(2))) == 1
    assert intertwiners(spin_representation(2), spin_representation(1)) == []


def test_projectors_and_refusals() -> None:
    """Projectors of ½ ⊗ ½ have ranks 3 and 1; a non-diagonalizable matrix is refused."""
    e, f, h = tensor_representation(SL2, SL2)
    ranks = sorted(p.rank() for _, p in eigen_projectors(e * f + f * e + h * h / 2))
    assert ranks == [1, 3]
    with pytest.raises(CertificateError, match='diagonalizable'):
        eigen_projectors(matrix(QQ, [[1, 1], [0, 1]]))


def test_clebsch_gordan_decomposes_one_times_one() -> None:
    """1 ⊗ 1 = 2 ⊕ 1 ⊕ 0, with T intertwining the product and the direct sum."""
    t, spins = clebsch_gordan(2, 2)
    assert spins == [4, 2, 0]
    product = tensor_representation(spin_representation(2), spin_representation(2))
    target = [block_diagonal_matrix([spin_representation(s)[k] for s in spins]) for k in range(3)]
    assert all(t * a == b * t for a, b in zip(product, target, strict=True))


def test_decomposition_refuses_a_non_invariant_summand() -> None:
    """A subspace that is not invariant cannot be a summand."""
    product = tensor_representation(SL2, SL2)
    one = identity_matrix(QQ, 4)
    with pytest.raises(CertificateError, match='not invariant'):
        decomposition(product, [one[:, :1], one[:, 1:]])


def test_relations_are_checked_in_sage_first() -> None:
    """A matrix list that is not a representation fails before Lean sees it."""
    e, f, h = SL2
    with pytest.raises(CertificateError, match='bracket relation'):
        representation_relations([e, f, 2 * h], TABLE)


def test_representation_facts_parse_in_lean(lean_parses: Callable[[list[Lean]], str]) -> None:
    """The emitted facts parse as Lean tactics."""
    product = tensor_representation(SL2, SL2)
    e, f, h = product
    projectors = [p for _, p in eigen_projectors(e * f + f * e + h * h / 2)]
    t, spins = clebsch_gordan(1, 1)
    target = [block_diagonal_matrix([spin_representation(s)[k] for s in spins]) for k in range(3)]
    one = identity_matrix(QQ, 2)
    facts = [
        representation_relations(SL2, TABLE, names=['e', 'f', 'h']),
        projector_facts(projectors, product),
        intertwining_facts(t, product, target),
        change_of_basis_facts(one, SL2, SL2),
    ]
    assert lean_parses(facts) == ''
