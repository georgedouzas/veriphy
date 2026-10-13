"""Test WZ pairs, Gosper sums and recurrences."""

import importlib.util
from collections.abc import Callable

import pytest
import sympy as sp

from veriphy.core import CertificateError
from veriphy.toolkit import (
    Lean,
    gosper_closed_form,
    gosper_proof,
    guess_recurrence,
    recurrence_proof,
    solve_recurrence,
    term_lean,
    wz_mate,
    wz_proof,
)
from veriphy.toolkit._summation import K, N


def test_wz_pair_satisfies_the_telescoping_identity() -> None:
    """F(n+1, k) - F(n, k) = G(n, k+1) - G(n, k) for the binomial WZ pair."""
    f = sp.binomial(N, K) / 2**N
    g = wz_mate(f)
    difference = f.subs(N, N + 1) - f - (g.subs(K, K + 1) - g)
    assert sp.simplify(sp.combsimp(difference)) == 0


def test_gosper_and_its_refusal() -> None:
    """Σ k·k! = n! - 1; Σ 1/k has no hypergeometric closed form."""
    assert sp.combsimp(gosper_closed_form(K * sp.factorial(K))) == sp.factorial(N) - 1
    with pytest.raises(CertificateError, match='Gosper-summable'):
        gosper_closed_form(1 / (K + 1))


def test_recurrences() -> None:
    """a(n+2) = 5a(n+1) - 6a(n) gives 3ⁿ - 2ⁿ; a missing initial value is refused."""
    assert sp.expand(solve_recurrence([-6, 5], [0, 1]) - (3**N - 2**N)) == 0
    with pytest.raises(CertificateError, match='initial conditions'):
        recurrence_proof(2, 'hrec', ['h0'])


@pytest.mark.skipif(importlib.util.find_spec('ore_algebra') is not None, reason='ore_algebra is installed')
def test_missing_ore_algebra_names_the_install_command() -> None:
    """Guessing a holonomic recurrence without ore_algebra names `sage -pip install ore_algebra`."""
    with pytest.raises(CertificateError, match='sage -pip install ore_algebra'):
        guess_recurrence([1, 1, 2, 5, 14, 42])


def test_summation_proofs_parse_in_lean(lean_parses: Callable[[list[Lean]], str]) -> None:
    """The proofs parse as Lean tactics."""
    assert term_lean(sp.factorial(K)) == 'fun (n k : ℕ) => ((k).factorial : ℚ)'
    proofs = [wz_proof(sp.binomial(N, K), 2**N, '(2 : ℚ) ^ n'), gosper_proof(), recurrence_proof(2, 'h', ['a', 'b'])]
    assert lean_parses(proofs) == ''
