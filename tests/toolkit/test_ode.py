"""Test proving ODE solutions by differentiation, on problems Lean extracted."""

import json
from collections.abc import Callable
from pathlib import Path

import pytest
from sage.all import SR, cos, diff, exp, function, sin

from veriphy.core import CertificateError
from veriphy.toolkit import Lean, derivative_order, read_problem, solve_exists, verify_definition

FIXTURES = Path(__file__).parent / 'fixtures'
DEFINITION = read_problem(json.loads((FIXTURES / 'ode_definition.json').read_text()))
EXISTS = read_problem(json.loads((FIXTURES / 'ode_exists.json').read_text()))


def test_derivative_order_counts_the_highest_derivative() -> None:
    """Return 2 for the harmonic oscillator and 0 when the function is not differentiated."""
    t, f = SR.var('t'), function('F_x')
    assert derivative_order(diff(f(t), t, 2) + f(t), 'F_x') == 2
    assert derivative_order(f(t) + diff(f(t), t), 'F_y') == 0


def test_definition_is_substituted_and_differentiated_twice() -> None:
    """Substitute `hx`, state two derivative facts about the stated lambda, and rewrite with both."""
    proof = str(verify_definition(DEFINITION))
    assert proof.startswith('subst hx\n')
    assert 'have d1 : deriv (fun s => A * Real.cos (ω * s) + B * Real.sin (ω * s)) =' in proof
    assert 'have d2 :' in proof
    assert 'simp only [d1, d2]' in proof


def test_existential_witness_is_sage_solution() -> None:
    """Supply Sage's solution with the initial conditions as the witness, and prove the three conjuncts."""
    proof = str(solve_exists(EXISTS))
    assert 'exact ⟨fun s => x₀ * (Real.cos (s * ω)) + (v₀ * (Real.sin (s * ω)) / ω), fun t => by' in proof
    assert proof.count('by (first | (norm_num [d1, d2]; done)') == 2


def test_stated_solution_replaces_sage() -> None:
    """Use a supplied solution body instead of solving."""
    s = SR.var('s_')
    omega, x0, v0 = (EXISTS.symbols[v] for v in ('x1', 'x2', 'x3'))
    proof = str(solve_exists(EXISTS, solution=x0 * cos(omega * s) + v0 / omega * sin(omega * s)))
    assert 'exact ⟨fun s => ' in proof


def test_wrong_solution_leaves_the_residual_for_lean() -> None:
    """End each equation's closer with a bare `ring_nf`, so Lean shows the residual of a wrong solution."""
    proof = str(solve_exists(EXISTS, solution=exp(SR.var('s_'))))
    assert '| ring_nf)' in proof


def test_goal_without_definition_or_existential_is_refused() -> None:
    """Fail naming what is missing when the goal neither has a defined function nor is an existential."""
    with pytest.raises(CertificateError, match='defines a function'):
        verify_definition(EXISTS)
    with pytest.raises(CertificateError, match='not an existential'):
        solve_exists(DEFINITION)


def test_ode_proofs_parse_in_lean(lean_parses: Callable[[list[Lean]], str]) -> None:
    """Both emitted proofs parse as Lean tactics."""
    assert lean_parses([verify_definition(DEFINITION), solve_exists(EXISTS)]) == ''
