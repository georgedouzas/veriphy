"""Summation certificates: WZ pairs, Gosper antidifferences and recurrences, with telescoping and induction proofs.

Sympy's Gosper algorithm finds the certificates; Lean checks the summand identity (`field_simp` and `ring` after the
binomial and factorial recurrences), sums it by `Finset.sum_range_sub`, and concludes by induction. Hypergeometric
terms are given as sympy expressions in `n` and `k` built from rationals, powers, `binomial` and `factorial`.
"""

import importlib
from collections.abc import Sequence

import sympy as sp
from sage.all import QQ, PolynomialRing
from sympy.concrete.gosper import gosper_sum, gosper_term

from veriphy.core import CertificateError
from veriphy.toolkit._lean import Lean, tactic

N, K = sp.symbols('n k', integer=True, nonnegative=True)
ORE_ALGEBRA = 'sage -pip install ore_algebra'


def _sympy(e: object) -> sp.Expr:
    """Return an expression as sympy over this module's `n` and `k` (a script's Sage integers mixed in are re-read)."""
    return sp.sympify(str(e), locals={'n': N, 'k': K})


def _render_atom(e: sp.Expr, guards: list[str]) -> str | None:
    """Return a number, symbol, binomial or factorial as Lean text over ℚ; `None` for anything else."""
    if e.is_Integer or e.is_Symbol:
        return f'({e} : ℚ)'
    if e.is_Rational:
        return f'(({e.p} : ℚ) / {e.q})'
    if isinstance(e, sp.binomial):
        top, bottom = e.args
        offset, rest = bottom.as_coeff_Add()
        if offset < 0:
            # a shifted lower index is negative, so the binomial zero, below the shift
            guards.append(f'{rest} < {-offset}')
        return f'(({_nat(top)}).choose ({_nat(bottom)}) : ℚ)'
    if isinstance(e, sp.factorial):
        return f'(({_nat(e.args[0])}).factorial : ℚ)'
    return None


def _render(e: sp.Expr, guards: list[str]) -> str:
    """Return a hypergeometric expression as Lean text over ℚ, collecting the guards its shifted binomials need."""
    e = sp.sympify(e)
    atom = _render_atom(e, guards)
    if atom is not None:
        return atom
    if e.is_Add or e.is_Mul:
        joiner = ' + ' if e.is_Add else ' * '
        return '(' + joiner.join(_render(a, guards) for a in e.args) + ')'
    if e.is_Pow:
        base, exponent = e.args
        if exponent.could_extract_minus_sign():
            positive = -exponent
            power = f'({_nat(positive)})' if positive.free_symbols else str(positive)
            return f'({_render(base, guards)} ^ {power})⁻¹'
        power = f'({_nat(exponent)})' if exponent.free_symbols else str(exponent)
        return f'({_render(base, guards)} ^ {power})'
    message = f'cannot render {e} for Lean (use rationals, powers, binomial and factorial)'
    raise CertificateError(message)


def _nat(e: sp.Expr) -> str:
    """Return an integer-valued expression in `n` and `k` as Lean text at ℕ."""
    return str(sp.sympify(e)).replace('**', ' ^ ')


def term_lean(e: sp.Expr) -> str:
    """Return a hypergeometric term as a Lean lambda `fun n k => …` over ℚ, zero where a shifted binomial is negative.

    Args:
        e: The term, in the symbols `n`, `k` of this module.

    Returns:
        The lambda.

    Examples:
        >>> print(term_lean(-sp.binomial(N, K - 1) / (2 * 2**N)))
        fun (n k : ℕ) => if k < 1 then 0 else (((-1 : ℚ) / 2) * ((2 : ℚ) ^ (n))⁻¹ * ((n).choose (k - 1) : ℚ))
    """
    guards: list[str] = []
    body = _render(e, guards)
    if guards:
        return f'fun (n k : ℕ) => if {" ∨ ".join(guards)} then 0 else {body}'
    return f'fun (n k : ℕ) => {body}'


def wz_mate(f: sp.Expr) -> sp.Expr:
    """Return the WZ mate `G` of a summand `F(n, k)` with `Σₖ F(n, k)` constant in `n`.

    `G` satisfies `F(n + 1, k) - F(n, k) = G(n, k + 1) - G(n, k)`; it is Gosper's antidifference in `k` of the left
    side.

    Args:
        f: The normalized summand (its sum over `k` is 1 for every `n`).

    Returns:
        `G`, simplified to a hypergeometric term.

    Raises:
        CertificateError: If the difference is not Gosper-summable (no WZ pair).

    Examples:
        >>> wz_mate(sp.binomial(N, K) / 2**N)
        -binomial(n, k - 1)/(2*2**n)
    """
    f = _sympy(f)
    difference = sp.combsimp(f.subs(N, N + 1) - f)
    ratio = gosper_term(difference, K)
    if ratio is None:
        message = 'F(n + 1, k) - F(n, k) is not Gosper-summable in k: no WZ pair'
        raise CertificateError(message)
    return sp.combsimp(ratio * difference)


def wz_proof(f: sp.Expr, closed_form: sp.Expr, closed_form_lean: str, mate: sp.Expr | None = None) -> Lean:
    """Return a proof of `∑ k ∈ Finset.range (n + 1), F n k = S n` (with `n` in scope) by a WZ pair.

    The normalized summand `F / S` sums to 1: the summand identity telescopes, the sum is constant in `n`, and it is 1
    at `n = 0`. `F` must vanish at `k = n + 1` (natural boundaries), and `S n ≠ 0` closes by `positivity`.

    Args:
        f: The summand `F(n, k)` (sympy, over `n`, `k`).
        closed_form: `S(n)` (sympy, over `n`).
        closed_form_lean: The Lean text of `S n` as the goal writes it, in `n`.
        mate: The WZ mate of `F / S`; found by Gosper's algorithm when `None`.

    Returns:
        The tactic.
    """
    f = _sympy(f)
    normalized = sp.combsimp(f / _sympy(closed_form))
    mate = wz_mate(normalized) if mate is None else mate
    lines = [
        f'let F : ℕ → ℕ → ℚ := fun n k => ({term_lean(f)}) n k * ({closed_form_lean})⁻¹',
        f'let G : ℕ → ℕ → ℚ := {term_lean(mate)}',
        'have hwz : ∀ n k, F (n + 1) k - F n k = G n (k + 1) - G n k := by',
        '  intro n k',
        '  rcases k with _ | k',
        '  all_goals simp [F, G, Nat.choose_succ_succ\', Nat.factorial_succ, pow_succ]',
        '  all_goals first | ring1 | (field_simp; ring1) | (field_simp; done)',
        'have hstep : ∀ n, ∑ k ∈ Finset.range (n + 2), F (n + 1) k = ∑ k ∈ Finset.range (n + 1), F n k := by',
        '  intro n',
        '  have hdiff : ∑ k ∈ Finset.range (n + 2), (F (n + 1) k - F n k) = 0 := by',
        '    rw [Finset.sum_congr rfl fun k _ => hwz n k, Finset.sum_range_sub]',
        '    simp [G]',
        '  rw [Finset.sum_sub_distrib, sub_eq_zero] at hdiff',
        '  rw [hdiff, Finset.sum_range_succ]',
        '  simp [F, Nat.choose_succ_self]',
        'have hone : ∀ n, ∑ k ∈ Finset.range (n + 1), F n k = 1 := by',
        '  intro n',
        '  induction n with',
        '  | zero => simp [F]',
        '  | succ n ih => rw [hstep, ih]',
        'have h := hone n',
        'simp only [F, ← Finset.sum_mul] at h',
        'simpa using (mul_inv_eq_one₀ (by positivity)).mp h',
    ]
    return tactic('\n'.join(lines))


def gosper_closed_form(f: sp.Expr) -> sp.Expr:
    """Return `Σ_{k<n} f(k)` in closed form by Gosper's algorithm.

    Args:
        f: The summand in `k` (and parameters).

    Returns:
        The closed form in `n`.

    Raises:
        CertificateError: If the sum is not Gosper-summable.

    Examples:
        >>> sp.combsimp(gosper_closed_form(K * sp.factorial(K)))
        factorial(n) - 1
    """
    closed = gosper_sum(_sympy(f), (K, 0, N - 1))
    if closed is None:
        message = f'{f} is not Gosper-summable: no hypergeometric closed form'
        raise CertificateError(message)
    return closed


def gosper_proof() -> Lean:
    """Return the induction proving `∑ k ∈ Finset.range n, f k = S n` once Sage has checked `S` is the antidifference.

    Returns:
        The tactic: induction on `n`, `Finset.sum_range_succ`, the factorial and power recurrences, `ring`.
    """
    return tactic(
        'induction n with\n'
        '| zero => simp\n'
        '| succ n ih => rw [Finset.sum_range_succ, ih]; push_cast [Nat.factorial_succ, pow_succ]; ring',
    )


def solve_recurrence(coefficients: Sequence[object], initial: Sequence[object]) -> sp.Expr:
    """Return the closed form of `a(n + d) = c₀ a(n) + … + c_{d-1} a(n + d - 1)` with initial values.

    Args:
        coefficients: `c₀, …, c_{d-1}`, constants or polynomials in `n`.
        initial: `a(0), …, a(d - 1)`.

    Returns:
        The closed form in `n`.

    Raises:
        CertificateError: If sympy finds none.

    Examples:
        >>> solve_recurrence([-6, 5], [0, 1])
        -2**n + 3**n
    """
    a = sp.Function('a')
    d = len(coefficients)
    equation = a(N + d) - sum(_sympy(c) * a(N + i) for i, c in enumerate(coefficients))
    solution = sp.rsolve(equation, a(N), {a(i): v for i, v in enumerate(initial)})
    if solution is None:
        message = 'no closed form for the recurrence; guess one with guess_recurrence and check it'
        raise CertificateError(message)
    return sp.simplify(solution)


def recurrence_proof(order: int, recurrence: str, initial: Sequence[str]) -> Lean:
    """Return a proof of a goal `a n = f n` by strong induction, from a recurrence of order `d` and `d` initial values.

    Args:
        order: The recurrence's order `d`.
        recurrence: The name of the hypothesis `∀ n, a (n + d) = …`.
        initial: The names of the hypotheses `a 0 = …`, …, `a (d - 1) = …`.

    Returns:
        The tactic.

    Raises:
        CertificateError: If the number of initial conditions is not the order.

    Examples:
        >>> print(recurrence_proof(2, 'hrec', ['h0', 'h1']))
        induction n using Nat.strong_induction_on with
        | _ n ih =>
          match n with
          | 0 => rw [h0]; norm_num
          | 1 => rw [h1]; norm_num
          | m + 2 => rw [hrec, ih m (by omega), ih (m + 1) (by omega)]; ring
    """
    if len(initial) != order:
        message = f'a recurrence of order {order} needs {order} initial conditions, got {len(initial)}'
        raise CertificateError(message)
    values = ''.join(f', ih {"m" if i == 0 else f"(m + {i})"} (by omega)' for i in range(order))
    cases = [f'  | {i} => rw [{h}]; norm_num' for i, h in enumerate(initial)]
    lines = [
        'induction n using Nat.strong_induction_on with',
        '| _ n ih =>',
        '  match n with',
        *cases,
        f'  | m + {order} => rw [{recurrence}{values}]; ring',
    ]
    return tactic('\n'.join(lines))


def guess_recurrence(terms: Sequence[object], order: int = 2) -> object:
    """Guess a holonomic recurrence for a sequence from its first terms, with `ore_algebra`.

    Args:
        terms: The first terms of the sequence.
        order: The order of the recurrence sought.

    Returns:
        The guessed operator (an `ore_algebra` object).

    Raises:
        CertificateError: If `ore_algebra` is not installed (naming the command) or nothing is found.
    """
    try:
        guess = importlib.import_module('ore_algebra').guess
    except ImportError:
        message = f'guessing a holonomic recurrence needs the ore_algebra package: {ORE_ALGEBRA}'
        raise CertificateError(message) from None
    ring = PolynomialRing(QQ, 'n')
    try:
        return guess(list(terms), ring, order=order)
    except ValueError:
        message = 'no recurrence of this order fits the terms; give more terms or raise the order'
        raise CertificateError(message) from None
