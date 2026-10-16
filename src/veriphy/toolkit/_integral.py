"""Definite integrals by the fundamental theorem of calculus: Sage finds an antiderivative, Lean checks it.

For a goal `∫ x in a..b, f x = v`, Sage integrates `f` symbolically and checks both the antiderivative `F` (`F' = f`)
and the value (`F b - F a = v`). Lean proves `HasDerivAt F (f x) x` on the interval from mathlib's derivative lemmas
(`has_deriv_at`), applies `intervalIntegral.integral_eq_sub_of_hasDerivAt` with continuity of `f` by `fun_prop`, and
evaluates `F b - F a`. Sines and cosines at integer multiples of `π` are stated as facts first, since `norm_num`
does not evaluate them.
"""

import re

from sage.all import SR, integrate, pi
from sage.symbolic.expression import Expression

from veriphy.core import CertificateError
from veriphy.toolkit._derivative import has_deriv_at
from veriphy.toolkit._lean import Lean, tactic
from veriphy.toolkit._problem import Integral, Problem
from veriphy.toolkit._symbolic_emit import symbolic

# the variable of the antiderivative, rendered `x_veriphy`: a name no goal uses
VARIABLE = 'x_veriphy_'
DERIVATIVE_CLOSE = (
    'first | ring1 | (field_simp; ring1) | (simp only [Real.cos_sq, Real.sin_sq_eq_half_sub]; ring1) '
    '| (simp only [Real.sin_two_mul, Real.cos_two_mul]; ring1) | (simp; ring1)'
)
FUNCTION_CLOSE = 'beta_reduce; first | rfl | ring1 | (simp; ring1) | (simp; done) | (field_simp; ring1)'
VALUE_CLOSE = 'all_goals first | (norm_num; done) | ring1 | (field_simp; ring1) | (simp; done)'


def _lean(e: Expression, problem: Problem) -> str:
    """Return a real expression's Lean text, unascribed."""
    return str(symbolic(e, problem, lean_type='ℝ'))


def _at(text: str, point: str) -> str:
    """Return a Lean text in the antiderivative's variable, evaluated at a point (the bound's own Lean text)."""
    return re.sub(rf'\b{VARIABLE[:-1]}\b', f'({point})', text)


def _subterms(e: Expression) -> list[Expression]:
    """Return every sub-expression of `e`, `e` included."""
    found = [e]
    for operand in e.operands():
        found += _subterms(operand)
    return found


def _endpoint_facts(
    antiderivative: Expression,
    x: Expression,
    bounds: list[tuple[Expression, str]],
    problem: Problem,
) -> list[str]:
    """Return facts for `sin` and `cos` of the antiderivative at the bounds when the argument is `k π`, `k ≥ 0`."""
    facts = []
    for kernel in _subterms(antiderivative):
        operator = kernel.operator()
        name = getattr(operator, 'name', lambda: '')() if operator is not None else ''
        if name not in ('sin', 'cos'):
            continue
        argument = kernel.operands()[0]
        for bound, text in bounds:
            k = (argument.subs({x: bound}) / pi).simplify_full()
            if not (k.is_integer() and k >= 0):
                continue
            term = _at(_lean(argument, problem), text)
            rewrite = f'rw [show ({term} : ℝ) = (({k} : ℕ) : ℝ) * Real.pi by push_cast; ring'
            if k == 0:
                # at zero the value is `simp`'s; rewriting `0` would also rewrite the fact's right side
                value = 0 if name == 'sin' else 1
                facts.append(f'Real.{name} ({term}) = {value} := by simp')
            elif name == 'sin':
                facts.append(f'Real.sin ({term}) = 0 := by\n  {rewrite}]; exact Real.sin_nat_mul_pi {k}')
            else:
                facts.append(f'Real.cos ({term}) = {(-1) ** int(k)} := by\n  {rewrite}, Real.cos_nat_mul_pi]; norm_num')
    return [f'have he{i} : {fact}' for i, fact in enumerate(dict.fromkeys(facts))]


def definite_integral_proof(problem: Problem, index: int = 0) -> Lean:
    """Return a proof of a goal `∫ x in a..b, f x = v` from an antiderivative Sage finds.

    Args:
        problem: The problem; the goal states the integral's value.
        index: Which of the goal's interval integrals (in the order the translation met them).

    Returns:
        The tactic.

    Raises:
        CertificateError: If the goal has no integral, Sage finds no elementary antiderivative, or the value is wrong.
    """
    if index >= len(problem.integrals):
        message = 'the goal has no interval integral the translation could read (∫ x in a..b, f x)'
        raise CertificateError(message)
    integral: Integral = problem.integrals[index]
    if integral.body is None or integral.lower is None or integral.upper is None:
        message = 'the integrand or a bound has no symbolic form'
        raise CertificateError(message)
    x = SR.var(VARIABLE)
    body = integral.body.subs({integral.var: x})
    antiderivative = integrate(body, x)
    if antiderivative.has(SR.var('integrate')) or 'integrate' in str(antiderivative):
        message = f'Sage finds no elementary antiderivative of {body}'
        raise CertificateError(message)
    if not bool((antiderivative.diff(x) - body).simplify_full() == 0):
        message = f'the antiderivative {antiderivative} does not differentiate back to {body}'
        raise CertificateError(message)
    goal = problem.goal
    if goal is None or goal.expr is None or not bool(SR(goal.expr).simplify_full() == 0):
        value = (antiderivative.subs({x: integral.upper}) - antiderivative.subs({x: integral.lower})).simplify_full()
        message = f'the integral is {value}, not the goal\'s value'
        raise CertificateError(message)
    variable = VARIABLE[:-1]
    f_text = f'fun {variable} => {_lean(antiderivative, problem)}'
    derivative = has_deriv_at(antiderivative, x, x, problem)
    interval = f'Set.uIcc ({integral.lower_text} : ℝ) ({integral.upper_text} : ℝ)'
    bounds = [(integral.lower, integral.lower_text), (integral.upper, integral.upper_text)]
    statement = f'HasDerivAt ({f_text}) (({integral.function}) {variable}) {variable}'
    lines = [
        f'have hF : ∀ {variable} ∈ {interval}, {statement} := by',
        f'  intro {variable} _',
        '  beta_reduce',
        # the derivative lemmas build Sage's form of the antiderivative; it equals the rendered one pointwise
        f'  refine (({derivative}).congr_of_eventuallyEq (Filter.Eventually.of_forall fun y => ?_)).congr_deriv ?_',
        f'  · {FUNCTION_CLOSE}',
        f'  · {DERIVATIVE_CLOSE}',
        f'rw [intervalIntegral.integral_eq_sub_of_hasDerivAt (f := {f_text}) (f\' := {integral.function}) hF',
        '  (by apply Continuous.intervalIntegrable; fun_prop)]',
        'beta_reduce',
    ]
    facts = _endpoint_facts(antiderivative, x, bounds, problem)
    lines += facts
    if facts:
        lines.append(f'simp only [{", ".join(f"he{i}" for i in range(len(facts)))}]')
    lines.append(VALUE_CLOSE)
    return tactic('\n'.join(lines))
