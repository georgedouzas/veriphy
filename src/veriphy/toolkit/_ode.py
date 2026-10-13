"""Prove that explicit functions solve ordinary differential equations, by differentiation rather than trust."""

import textwrap
from collections.abc import Mapping

from sage.all import SR, assume, desolve, diff, forget, solve
from sage.symbolic.expression import Expression
from sage.symbolic.operators import FDerivativeOperator

from veriphy.core import CertificateError
from veriphy.toolkit._derivative import has_deriv_at_proof
from veriphy.toolkit._lean import Lean, tactic
from veriphy.toolkit._problem import Problem
from veriphy.toolkit._symbolic_emit import symbolic

CLOSE = (
    'first | ring1 | (ring_nf; done) | (field_simp; done) | (field_simp; ring1) | (field_simp; ring_nf; done)'
    ' | (norm_num; done)'
)
# the last alternative leaves the normalized residual of a wrong solution for Lean to show
EQUATION_CLOSE = f'{CLOSE} | ring_nf'
CONDITION_CLOSE = 'first | (norm_num [{names}]; done) | (simp only [{names}]; field_simp; done) | (field_simp; done)'


def derivative_order(expr: Expression, function: str) -> int:
    """Return the highest order to which `expr` differentiates the unknown function named `function`.

    Args:
        expr: A symbolic expression.
        function: The Sage name of the unknown function.

    Returns:
        The order, 0 when the function is not differentiated.

    Examples:
        >>> from sage.all import function
        >>> t = SR.var('t'); f = function('F_x')
        >>> derivative_order(diff(f(t), t, 2) + f(t), 'F_x')
        2
    """
    best = 0
    stack = [SR(expr)]
    while stack:
        e = stack.pop()
        op = e.operator()
        if isinstance(op, FDerivativeOperator) and op.function().name() == function:
            best = max(best, len(op.parameter_set()))
        stack.extend(e.operands())
    return best


def _lambda(body: Expression, var: Expression, problem: Problem) -> str:
    """Return the Lean text `fun s => body` of a body in `var`."""
    return f'fun {str(var).rstrip("_")} => {symbolic(body, problem, lean_type="")}'


def derivative_chain(
    body: Expression,
    var: Expression,
    order: int,
    problem: Problem,
    *,
    function_text: str | None = None,
    proofs: Mapping[str, str] | None = None,
) -> tuple[list[Lean], list[str]]:
    """Return facts `dₖ : deriv (fun s => Bₖ₋₁) = fun s => Bₖ` for `k = 1 … order`, and their names.

    Each fact is proved at an arbitrary point by a composed `HasDerivAt` term. `function_text` states the first
    function as the goal writes it, so that rewriting with `d1` matches the goal.

    Args:
        body: The function's body `B₀`, in `var`.
        var: The variable, a Sage symbol ending in `_` (rendered without it).
        order: How many derivatives.
        problem: The problem whose atoms name the parameters.
        function_text: The Lean text of the first function, rendered from `body` when `None`.
        proofs: Tactics proving nonzero conditions no hypothesis states, by their Lean text.

    Returns:
        The facts and their names.
    """
    facts: list[Lean] = []
    names: list[str] = []
    point = str(var).rstrip('_')
    current, current_text = SR(body), function_text or _lambda(body, var, problem)
    for k in range(1, order + 1):
        nxt = diff(current, var)
        nxt_text = _lambda(nxt, var, problem)
        step = has_deriv_at_proof(current, var, var, nxt, problem, proofs=proofs, function=current_text, at=point)
        name = f'd{k}'
        facts.append(
            tactic(
                f'have {name} : deriv ({current_text}) = {nxt_text} := by\n'
                f'  funext {point}\n' + textwrap.indent(str(step), '  ') + '\n  exact hd.deriv',
            ),
        )
        names.append(name)
        current, current_text = nxt, nxt_text
    return facts, names


def verify_definition(problem: Problem, proofs: Mapping[str, str] | None = None) -> Lean:
    """Prove an ODE goal about a function defined explicitly by a hypothesis `x = fun s => …`.

    The proof substitutes the definition, states each derivative of the body as a fact, rewrites with them and closes
    the remaining identity by `ring1`, `field_simp` or `norm_num`.

    Args:
        problem: The problem; its goal is an equation in an unknown function that a hypothesis defines.
        proofs: Tactics proving nonzero conditions no hypothesis states, by their Lean text.

    Returns:
        The tactic block.

    Raises:
        CertificateError: If no hypothesis defines a function of the goal.
    """
    goal = problem.goal.expr if problem.goal is not None else None
    for definition in problem.definitions:
        f = problem.symbols[definition.function]
        if goal is None or definition.body is None or not SR(goal).find(f(SR.wild(0))):
            continue
        order = derivative_order(SR(goal), definition.function)
        facts, names = derivative_chain(
            definition.body,
            definition.var,
            order,
            problem,
            function_text=definition.text,
            proofs=proofs,
        )
        rewrite = [tactic(f'simp only [{", ".join(names)}]')] if names else []
        lines = [tactic(f'subst {definition.hyp}'), *facts, *rewrite, tactic(EQUATION_CLOSE)]
        return tactic('\n'.join(str(line) for line in lines))
    message = 'no hypothesis `x = fun s => …` defines a function of the goal'
    raise CertificateError(message)


def _value_terms(e: Expression, function: str) -> list[tuple[int, Expression, Expression]]:
    """Return the terms `f⁽ᵏ⁾(c)` of `e` at constant points: order, point and the term itself."""
    found = []
    stack = [SR(e)]
    while stack:
        x = stack.pop()
        op = x.operator()
        if isinstance(op, FDerivativeOperator) and op.function().name() == function and not x.variables():
            found.append((len(op.parameter_set()), x.operands()[0], x))
        elif op is not None and getattr(op, 'name', lambda: '')() == function and x.operands()[0].is_constant():
            found.append((0, x.operands()[0], x))
        else:
            stack.extend(x.operands())
    return found


def _initial_values(conditions: list[Expression], function: str, order: int) -> list[Expression]:
    """Return `[t₀, y₀, y'₀, …]` for `desolve` from conditions `f(t₀) - y₀`, `f'(t₀) - y'₀`, …."""
    point = None
    values: list[Expression | None] = [None] * order
    u = SR.var('u_')
    for e in conditions:
        for k, at, term in _value_terms(e, function):
            solved = solve(SR(e).subs({term: u}) == 0, u)
            if k < order and solved:
                values[k] = solved[0].rhs()
                point = at
    if point is None or any(v is None for v in values):
        message = f'need {order} initial conditions at one point to solve the equation'
        raise CertificateError(message)
    return [point, *values]


def _assumptions(problem: Problem) -> list[Expression]:
    """Return the problem's sign and nonzero hypotheses as Sage assumptions (`ω ≠ 0` for `hω : ω ≠ 0`)."""
    relations = {'ne': lambda e: e != 0, 'lt': lambda e: e < 0, 'le': lambda e: e <= 0}
    return [relations[h.rel](h.expr) for h in problem.hyps if h.expr is not None and h.rel in relations]


def solve_exists(
    problem: Problem,
    proofs: Mapping[str, str] | None = None,
    solution: Expression | None = None,
) -> Lean:
    """Prove `∃ x, (∀ t, ODE) ∧ conditions` by solving the equation with Sage and checking the solution.

    Sage's `desolve` finds the solution with the initial conditions (or `solution` is used, a body in `s_`); the proof
    supplies it as the witness, states its derivatives as facts, and closes each conjunct.

    Args:
        problem: The problem; its goal is an existential over an unknown function.
        proofs: Tactics proving nonzero conditions no hypothesis states, by their Lean text.
        solution: A solution body in the variable `s_`, instead of Sage's.

    Returns:
        The tactic.

    Raises:
        CertificateError: If the goal is not such an existential, or Sage finds no solution.
    """
    ef = problem.exists_function
    if ef is None:
        message = 'the goal is not an existential over an unknown function'
        raise CertificateError(message)
    f = problem.symbols[ef.function]
    t, s = SR.var('t'), SR.var('s_')
    equations = [e.subs({v: t}) for v, e in ef.conjuncts if v is not None and e is not None]
    conditions = [e for v, e in ef.conjuncts if v is None and e is not None]
    if not equations:
        message = 'the existential has no equation `∀ t, …` in the function'
        raise CertificateError(message)
    order = max(derivative_order(e, ef.function) for e in equations)
    if solution is None:
        ics = _initial_values(conditions, ef.function, order) if conditions else None
        assumed = _assumptions(problem)
        assume(*assumed) if assumed else None
        try:
            found = desolve(equations[0] == 0, f(t), ics=ics, ivar=t)
        finally:
            forget(*assumed) if assumed else None
        solution = SR(found).subs({t: s})
    facts, names = derivative_chain(solution, s, order, problem, proofs=proofs)
    witness = _lambda(solution, s, problem)
    listed = ', '.join(names)
    # each proof is parenthesized: a printed replacement may break its line after `;`, which `by` alone rejects
    parts = []
    for v, _ in ef.conjuncts:
        rewrite = f'simp only [{listed}]; ' if names else ''
        if v is not None:
            parts.append(f'fun {str(v).rstrip("_")} => by ({rewrite}{EQUATION_CLOSE})')
        else:
            parts.append(f'by ({CONDITION_CLOSE.format(names=listed)})' if names else 'by norm_num')
    lines = [*facts, tactic(f'exact ⟨{witness}, {", ".join(parts)}⟩')]
    return tactic('\n'.join(str(line) for line in lines))
