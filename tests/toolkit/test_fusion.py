"""Test fusion data from Sage, the pentagon and hexagon checks, gauges and the facts emitted for them."""

from collections.abc import Callable

import pytest
from sage.all import QQ, QuadraticField

from veriphy.core import CertificateError
from veriphy.toolkit import (
    Fusion,
    Lean,
    associativity_violations,
    coefficients,
    fibonacci,
    find_gauge,
    fusion_data_term,
    fusion_facts,
    fusion_proof,
    fusion_rules,
    gauge_facts,
    gauge_mismatch,
    gauge_proof,
    gauge_transform,
    hexagon_violations,
    ising,
    pentagon_violations,
    root_fact,
)


def test_su2_level_2_rules() -> None:
    """SU(2) at level 2: σ ⊗ σ = 1 + ψ, σ ⊗ ψ = σ, ψ ⊗ ψ = 1, associative and self-dual."""
    rules = fusion_rules('A1', 2)
    assert rules.rules[(1, 1)] == [0, 2]
    assert rules.rules[(1, 2)] == [1]
    assert rules.rules[(2, 2)] == [0]
    assert rules.dual == [0, 1, 2]
    assert associativity_violations(rules) == []


def test_multiplicities_are_refused() -> None:
    """SU(3) at level 3 has a multiplicity 2: outside the multiplicity-free asset."""
    with pytest.raises(CertificateError, match='multiplicity above 1'):
        fusion_rules('A2', 3)


def test_fibonacci_and_ising_satisfy_the_equations() -> None:
    """Fibonacci's F-symbols solve every pentagon; Ising's F- and R-symbols every pentagon and hexagon."""
    assert pentagon_violations(fibonacci()) == 0
    assert (pentagon_violations(ising()), hexagon_violations(ising())) == (0, 0)


def test_wrong_symbols_are_counted() -> None:
    """Trivial F-symbols on the Fibonacci rules fail pentagons; flipping an Ising R-symbol fails hexagons."""
    fib = fibonacci()
    assert pentagon_violations(Fusion(fib.labels, fib.dual, fib.rules, field='sqrt5')) > 0
    data = ising()
    data.r_values[(1, 1, 0)] = -data.r_values[(1, 1, 0)]
    assert hexagon_violations(data) > 0
    with pytest.raises(CertificateError, match='hexagon equations fail'):
        fusion_proof(data, braided=True)


def test_coefficients_on_the_power_basis() -> None:
    """Values become rational coefficients on the power basis, trailing zeros dropped, zero empty."""
    assert coefficients(QuadraticField(5, 's').gen() / 2 - 1, 'sqrt5') == [-1, QQ(1) / 2]
    assert coefficients(0, 'zeta16') == []
    assert coefficients(QQ(3), 'rational') == [3]


def test_gauge_transformations_are_found() -> None:
    """A gauge preserves the equations, and find_gauge recovers one relating the data; other data are not related."""
    fib = fibonacci()
    other = gauge_transform(fib, {(1, 1, 1): 2})
    assert pentagon_violations(other) == 0
    u = find_gauge(fib, other)
    assert u is not None
    assert gauge_transform(fib, u).f_values == other.f_values
    assert gauge_mismatch(fib, fib) == 'the data agree: no gauge transformation needed'
    assert 'gauge: u[(1, 1, 1)] = 2' in gauge_mismatch(fib, other)
    # the Galois conjugate (the Yang-Lee category) solves the pentagons too, but is not gauge equivalent
    values = {key: value.galois_conjugate() for key, value in fib.f_values.items()}
    conjugate = Fusion(fib.labels, fib.dual, fib.rules, values, {}, 'sqrt5')
    assert pentagon_violations(conjugate) == 0
    assert find_gauge(fib, conjugate) is None


def test_a_wrong_gauge_is_refused() -> None:
    """Facts for a gauge that does not relate the data are refused in Sage."""
    fib = fibonacci()
    other = gauge_transform(fib, {(1, 1, 1): 2})
    with pytest.raises(CertificateError, match='F-symbols'):
        gauge_facts(fib, other, {(1, 1, 1): 3})


def test_fusion_facts_parse_in_lean(lean_parses: Callable[[list[Lean]], str]) -> None:
    """The emitted facts and proofs parse as Lean tactics."""
    fib = fibonacci()
    other = gauge_transform(fib, {(1, 1, 1): 2})
    snippets = [
        fusion_facts(fusion_rules('A1', 2), braided=False, symbols=False),
        fusion_facts(fib, braided=False),
        fusion_proof(ising(), braided=True),
        gauge_proof(fib, other, {(1, 1, 1): 2}),
        root_fact('zeta16'),
    ]
    assert lean_parses(snippets) == ''
    assert fusion_data_term(fib).startswith('(let N : Fin 2 → Fin 2 → Fin 2 → ℕ := ')
