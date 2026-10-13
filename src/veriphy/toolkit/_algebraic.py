"""Infeasibility certificates for polynomial systems: Nullstellensatz, radical membership and Positivstellensatz.

Sage searches (Gröbner lifts, an exact LP over products of hypotheses and squares); Lean checks the identity the
certificate states, by `linear_combination` (which accepts inequality facts with nonnegative weights).
"""

import itertools
from collections.abc import Sequence

from sage.all import QQ
from sage.rings.polynomial.multi_polynomial import MPolynomial

from veriphy.core import CertificateError
from veriphy.toolkit._emit import hyp, linear_combination, refute
from veriphy.toolkit._lean import Lean, polynomial, tactic, term
from veriphy.toolkit._lp import solve_exact_lp
from veriphy.toolkit._problem import Hyp, Problem


def _equalities(problem: Problem) -> list[Hyp]:
    """Return the hypotheses that are polynomial equalities."""
    return [h for h in problem.hyps if h.rel == 'eq' and h.poly is not None and h.name]


def nullstellensatz_proof(problem: Problem) -> Lean:
    """Refute a system of polynomial equalities with no common zero: `1 = Σ gᵢ fᵢ`, from a Gröbner lift.

    Args:
        problem: The problem; its goal is `False` and its equality hypotheses have no common zero.

    Returns:
        The tactic.

    Raises:
        CertificateError: If 1 is not in the ideal of the equalities (they have a common zero over ℂ).

    Examples:
        >>> from veriphy.toolkit import read_problem
        >>> prob = read_problem({'vars': ['x0', 'x1'], 'atoms': ['x', 'y'], 'carrier': 'ℚ', 'goal': {'kind': 'false'},
        ...     'hyps': [{'name': 'hxy', 'rel': 'eq', 'poly': '(x0 * x1) - (1)', 'text': 'x * y = 1'},
        ...              {'name': 'hx', 'rel': 'eq', 'poly': '(x0) - (0)', 'text': 'x = 0'}]})
        >>> print(nullstellensatz_proof(prob))
        have h1 : (1 : ℚ) = 0 := by linear_combination (-1) * hxy + (y) * hx
        exact one_ne_zero h1
    """
    eqs = _equalities(problem)
    ideal = problem.ring.ideal([h.poly for h in eqs])
    if 1 not in ideal:
        message = 'the equalities have a common zero over ℂ: 1 is not in their ideal'
        raise CertificateError(message)
    cofactors = problem.ring(1).lift(ideal)
    combination = linear_combination([(c, hyp(problem, h.name)) for c, h in zip(cofactors, eqs, strict=True)], problem)
    carrier = problem.carrier or 'ℚ'
    return tactic(f'have h1 : (1 : {carrier}) = 0 := by {combination}\nexact one_ne_zero h1')


def radical_proof(problem: Problem, max_power: int = 8) -> Lean:
    """Prove `p = 0` (the goal `lhs = rhs`) from equalities whose ideal contains a power `pᵏ`.

    Args:
        problem: The problem; its goal is a polynomial equality over a ring without zero divisors.
        max_power: The largest power tried.

    Returns:
        The tactic: `pᵏ = 0` by `linear_combination`, then `pow_eq_zero_iff`.

    Raises:
        CertificateError: If no power up to `max_power` is in the ideal.
    """
    goal = problem.goal
    if goal is None or goal.rel != 'eq' or goal.poly is None:
        message = 'the goal must be a polynomial equality'
        raise CertificateError(message)
    eqs = _equalities(problem)
    ideal = problem.ring.ideal([h.poly for h in eqs])
    for k in range(1, max_power + 1):
        if goal.poly**k in ideal:
            cofactors = (goal.poly**k).lift(ideal)
            weighted = [(c, hyp(problem, h.name)) for c, h in zip(cofactors, eqs, strict=True)]
            combination = linear_combination(weighted, problem)
            if k == 1:
                return tactic(str(combination))
            sides = f'({problem.lhs.text}) - ({problem.rhs.text})' if problem.lhs and problem.rhs else None
            if sides is None:
                message = 'the goal has no polynomial sides to state the power of'
                raise CertificateError(message)
            return tactic(
                f'have hk : ({sides}) ^ {k} = 0 := by {combination}\n'
                f'exact sub_eq_zero.mp ((pow_eq_zero_iff (n := {k}) (by norm_num)).mp hk)',
            )
    message = f'no power up to {max_power} of the goal is in the ideal of the equalities'
    raise CertificateError(message)


def _linear_forms(ring: object) -> list[MPolynomial]:
    """Return candidate square roots: each variable, and sums and differences of two variables."""
    gens = list(ring.gens())
    forms = list(gens)
    for a, b in itertools.combinations(gens, 2):
        forms += [a - b, a + b]
    return forms


def positivstellensatz_proof(
    problem: Problem,
    squares: Sequence[MPolynomial] | None = None,
    multiplier_degree: int = 1,
) -> Lean:
    """Refute a real semialgebraic system: `κ = Σ wₖ Pₖ + Σ hⱼ fⱼ` with every `Pₖ ≤ 0` and `κ > 0`.

    The facts `Pₖ` are the inequality hypotheses, their pairwise products and the given squares (by default squares of
    variables and of their sums and differences); the multipliers `hⱼ` of the equalities are polynomials. An exact LP
    finds the weights; `linear_combination` checks the identity.

    Args:
        problem: The problem; its goal is `False` (state a negated goal as a hypothesis first).
        squares: Polynomials whose squares may enter the certificate.
        multiplier_degree: The degree of the equality multipliers.

    Returns:
        The tactic.

    Raises:
        CertificateError: If no certificate of this degree exists.
    """
    ring = problem.ring
    ineqs = [h for h in problem.hyps if h.rel in ('le', 'lt') and h.poly is not None and h.name]
    eqs = _equalities(problem)
    # each fact: (polynomial P with P ≤ 0 or P < 0, strict, proof term)
    facts: list[tuple[MPolynomial, bool, Lean]] = [(h.poly, h.rel == 'lt', hyp(problem, h.name)) for h in ineqs]

    def nonneg(h: Hyp) -> str:
        return f'(sub_nonneg.mpr {h.name}.le)' if h.rel == 'lt' else f'(sub_nonneg.mpr {h.name})'

    for a, b in itertools.combinations_with_replacement(ineqs, 2):
        facts.append((-(a.poly * b.poly), False, term(f'mul_nonneg {nonneg(a)} {nonneg(b)}')))
    for s in squares if squares is not None else _linear_forms(ring):
        facts.append((-(ring(s) ** 2), False, term(f'sq_nonneg ({polynomial(ring(s), problem)})')))
    multipliers = [m for d in range(multiplier_degree + 1) for m in _monomials(ring, d)]
    columns: list[MPolynomial] = [p for p, _, _ in facts] + [m * h.poly for h in eqs for m in multipliers]
    n_facts = len(facts)
    monomials = sorted({m for p in columns for m in p.monomials()} - {ring(1)})
    rows = [([p.monomial_coefficient(m) for p in columns], 0) for m in monomials]
    constants = [p.constant_coefficient() for p in columns]
    nonneg_vars = list(range(n_facts))
    weights = solve_exact_lp(len(columns), eqs=rows, les=[([-c for c in constants], 1)], nonneg=nonneg_vars)
    strict = False
    if weights is None:
        strictness = [1 if s else 0 for _, s, _ in facts] + [0] * (len(columns) - n_facts)
        weights = solve_exact_lp(
            len(columns),
            eqs=[*rows, (constants, 0)],
            les=[([-s for s in strictness], 1)],
            nonneg=nonneg_vars,
        )
        strict = True
    if weights is None:
        message = 'no Positivstellensatz certificate of this degree; pass more squares or raise multiplier_degree'
        raise CertificateError(message)
    kappa = sum(w * c for w, c in zip(weights, constants, strict=True))
    weighted: list[tuple[object, Lean]] = [(w, proof) for w, (_, _, proof) in zip(weights, facts, strict=False) if w]
    eq_weights = weights[n_facts:]
    for j, h in enumerate(eqs):
        coefficient = sum(eq_weights[j * len(multipliers) + t] * m for t, m in enumerate(multipliers))
        if coefficient != 0:
            weighted.append((coefficient, hyp(problem, h.name)))
    uses_strict = strict or any(w and s for w, (_, s, _) in zip(weights, facts, strict=False))
    return refute(QQ(kappa), strict=uses_strict, weighted=weighted, problem=problem)


def _monomials(ring: object, degree: int) -> list[MPolynomial]:
    """Return the monomials of a given total degree."""
    gens = list(ring.gens())
    return [ring.prod(c) if c else ring(1) for c in itertools.combinations_with_replacement(gens, degree)]
