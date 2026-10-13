"""Test building `HasDerivAt` proof terms from Sage expressions."""

from collections.abc import Callable

import pytest
from sage.all import SR, diff, exp, log, sin

from veriphy.core import CertificateError
from veriphy.toolkit import Lean, has_deriv_at, has_deriv_at_proof, read_problem

PROBLEM = read_problem(
    {
        'vars': ['x0'],
        'atoms': ['a'],
        'carrier': 'ℝ',
        'hyps': [{'name': 'hq', 'text': 'a ^ 2 + 1 ≠ 0'}],
        'goal': {'kind': 'false'},
    },
)
a = PROBLEM.symbols['x0']
t = SR.var('t_')


def test_missing_side_condition_is_named() -> None:
    """Fail naming `a ≠ 0` for `log` at `a` when nothing states it."""
    with pytest.raises(CertificateError, match='a ≠ 0'):
        has_deriv_at(log(t), t, a, PROBLEM)


def test_side_conditions_from_hypotheses_and_proofs() -> None:
    """Pass a stated hypothesis by name and a supplied proof as a `by` block."""
    assert ' hq)' in str(has_deriv_at(t / (t**2 + 1), t, a, PROBLEM))
    assert '(by positivity)' in str(has_deriv_at(log(t), t, a, PROBLEM, proofs={'a ≠ 0': 'positivity'}))


def test_exponent_depending_on_the_variable_is_refused() -> None:
    """Refuse `t ^ t`, which needs a rewrite through `exp` and `log` first."""
    with pytest.raises(CertificateError, match='exponent'):
        has_deriv_at(t**t, t, a, PROBLEM)


def test_proof_unfolds_exactly_the_pointwise_operations_it_applies() -> None:
    """List only the `Pi` lemmas the term needs: none for a lambda product, more for an applied quotient."""
    product = str(
        has_deriv_at_proof(
            log(t) * sin(t),
            t,
            a,
            diff(log(t) * sin(t), t).subs({t: a}),
            PROBLEM,
            proofs={'a ≠ 0': 'positivity'},
        ),
    )
    assert 'simp only' not in product
    quotient = str(has_deriv_at_proof(t / (t**2 + 1), t, a, diff(t / (t**2 + 1), t).subs({t: a}), PROBLEM))
    assert 'simp only [Pi.add_apply, Pi.pow_apply]' in quotient


def test_derivative_terms_parse_in_lean(lean_parses: Callable[[list[Lean]], str]) -> None:
    """Every emitted term and proof parses as Lean."""
    snippets = [
        has_deriv_at(t**2 * exp(t), t, 1, PROBLEM),
        has_deriv_at(t / (t**2 + 1), t, a, PROBLEM),
        has_deriv_at_proof(exp(t**2 + t), t, a, diff(exp(t**2 + t), t).subs({t: a}), PROBLEM),
    ]
    assert lean_parses(snippets) == ''
