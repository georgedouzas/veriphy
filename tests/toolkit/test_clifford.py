"""Test gamma matrices, the Clifford relation, traces and Fierz coefficients."""

from collections.abc import Callable

import pytest
from sage.all import QQ, matrix

from veriphy.core import CertificateError
from veriphy.toolkit import (
    Lean,
    clifford_facts,
    clifford_violations,
    fierz_coefficients,
    fierz_fact,
    gamma5,
    gamma_matrices,
    gaussian_matrix_term,
)


@pytest.mark.parametrize('representation', ['dirac', 'weyl'])
@pytest.mark.parametrize('signature', ['mostly_minus', 'mostly_plus'])
def test_clifford_relation_and_gamma5(representation: str, signature: str) -> None:
    """Every representation and signature satisfies the Clifford relation; γ⁵ squares to 1 and anticommutes."""
    gammas, eta = gamma_matrices(representation, signature)
    assert clifford_violations(gammas, eta) == []
    g5 = gamma5(gammas, eta)
    assert g5 * g5 == 1
    assert all(g * g5 == -g5 * g for g in gammas)


def test_trace_of_four_gamma_matrices() -> None:
    """tr(γ^μ γ^ν γ^ρ γ^σ) = 4(η^{μν} η^{ρσ} - η^{μρ} η^{νσ} + η^{μσ} η^{νρ}) for every index."""
    gammas, eta = gamma_matrices()
    for m, n, r, s in [(0, 0, 1, 1), (0, 1, 0, 1), (1, 2, 2, 1), (3, 3, 3, 3)]:
        expected = 4 * (eta[m, n] * eta[r, s] - eta[m, r] * eta[n, s] + eta[m, s] * eta[n, r])
        assert (gammas[m] * gammas[n] * gammas[r] * gammas[s]).trace() == expected


def test_fierz_coefficients_are_an_involution() -> None:
    """Rearranging twice is the identity: C² = 1."""
    c = fierz_coefficients(*gamma_matrices())
    assert c * c == 1
    assert all(QQ(4 * x) in QQ for x in c.list())


def test_refusals() -> None:
    """A broken representation or an unknown name is refused."""
    gammas, eta = gamma_matrices()
    with pytest.raises(CertificateError, match='Clifford relation'):
        clifford_facts([2 * gammas[0], *gammas[1:]], eta)
    with pytest.raises(CertificateError, match='unknown representation'):
        gamma_matrices('majorana')
    with pytest.raises(CertificateError, match='Gaussian integer'):
        gaussian_matrix_term(matrix(QQ, [[QQ(1) / 2]]))


def test_clifford_facts_parse_in_lean(lean_parses: Callable[[list[Lean]], str]) -> None:
    """The facts parse as Lean tactics."""
    gammas, eta = gamma_matrices()
    assert lean_parses([clifford_facts(gammas, eta), fierz_fact(gammas, eta)[1]]) == ''
