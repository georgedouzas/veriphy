"""Test differential-operator and matrix-operator identities."""

from collections.abc import Callable

import pytest
from sage.all import I, QuadraticField, matrix, sqrt, var

from veriphy.core import CertificateError
from veriphy.toolkit import (
    Coordinates,
    Lean,
    canonical_commutator,
    commutator,
    complex_matrix_term,
    ladder_combination,
    ladder_commutator_proof,
    ladder_matrices,
    ladder_operators,
    operator_identity,
    operator_relations,
    real_matrix_term,
)


def test_canonical_commutator_and_its_failure() -> None:
    """[d/dx, x] = 1 holds; [d/dx, x] = 2 is refused with the difference."""
    c = Coordinates(1)
    d, x = c.partial(0), c.multiplication(c.symbols[0])
    proof = str(operator_identity(commutator(d, x), c.scalar(1), c))
    assert 'deriv' in proof
    with pytest.raises(CertificateError, match='differ by'):
        operator_identity(commutator(d, x), c.scalar(2), c)


def test_angular_momentum_needs_symmetry_and_second_order() -> None:
    """[L₁, L₂] = -L₃ uses the symmetry of second derivatives; third-order identities in several variables fail."""
    c = Coordinates(3)

    def angular(j: int, k: int) -> object:
        return c.multiplication(c.symbols[j]) * c.partial(k) - c.multiplication(c.symbols[k]) * c.partial(j)

    proof = str(operator_identity(commutator(angular(1, 2), angular(2, 0)), c.scalar(-1) * angular(0, 1), c))
    assert 'isSymmSndFDerivAt' in proof
    third = c.partial(0) * c.partial(1) * c.partial(2)
    with pytest.raises(CertificateError, match='second order'):
        operator_identity(third, third, c)


def test_pauli_relations_and_rendering() -> None:
    """Sage finds [σ₁, σ₂] = 2i σ₃ and renders ℚ(i) and √k entries for Lean."""
    i = QuadraticField(-1, 'i').gen()
    pauli = [matrix([[0, 1], [1, 0]]), matrix([[0, -i], [i, 0]]), matrix([[1, 0], [0, -1]])]
    facts = str(operator_relations(pauli, ['s1', 's2', 's3'], pairs=[(0, 1)]))
    assert '= (2 * Complex.I) • s3' in facts
    assert complex_matrix_term(pauli[1]).startswith('(!![0, (-1 * Complex.I); (Complex.I), 0]')
    a, _ = ladder_matrices(3)
    assert 'Real.sqrt 2' in real_matrix_term(a)
    with pytest.raises(CertificateError, match='span'):
        operator_relations(pauli[:2], ['s1', 's2'])


def test_operator_proofs_parse_in_lean(lean_parses: Callable[[list[Lean]], str]) -> None:
    """The operator facts parse as Lean tactics."""
    c = Coordinates(1)
    i = QuadraticField(-1, 'i').gen()
    pauli = [matrix([[0, 1], [1, 0]]), matrix([[0, -i], [i, 0]]), matrix([[1, 0], [0, -1]])]
    proofs = [
        operator_identity(commutator(c.partial(0), c.multiplication(c.symbols[0])), c.scalar(1), c),
        operator_relations(pauli, ['s1', 's2', 's3']),
    ]
    assert lean_parses(proofs) == ''


def test_ladder_commutators_from_the_canonical_relation() -> None:
    """[a, a†] = 1, [a, x] = ξ/√2 and [a + a†, p] = 2iℏ/(√2 ξ), in Physlib's convention."""
    xi, hbar = var('xi hbar')
    lowering, raising = ladder_operators()
    assert canonical_commutator(lowering, raising) == 1
    assert bool(canonical_commutator(lowering, {'x': 1}) == xi / sqrt(2))
    both = ladder_combination({'a': 1, 'a†': 1})
    assert bool(canonical_commutator(both, ladder_combination({'p': 1})) == 2 * I * hbar / (sqrt(2) * xi))


def test_ladder_refusals_and_proof_names() -> None:
    """Unknown operator names are refused; the proof names the goal's index and oscillator."""
    with pytest.raises(CertificateError, match='unknown operators'):
        ladder_combination({'n': 1})
    proof = str(ladder_commutator_proof(index='j', oscillator='H'))
    assert 'have hξ := H.ξ_ofReal_ne_zero j' in proof
    assert '← lie_skew (QuantumMechanics.momentumCLM j) (QuantumMechanics.positionCLM j)' in proof
