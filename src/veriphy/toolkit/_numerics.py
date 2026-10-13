"""Certified numerics: bounds on transcendental values and isolated real roots, checked exactly in Lean.

Bounds use mathlib's lemmas where they suffice (`Real.pi_gt_d6`, `Real.exp_one_lt_d9`, …) and otherwise mathlib's
series bounds with a rational remainder (`Real.exp_bound`, `Real.abs_log_sub_add_sum_range_le`, `Real.sin_bound`,
`Real.cos_bound`), whose truncation order Sage's interval arithmetic chooses. Roots of explicit polynomials are
isolated by Sage; Lean proves each interval holds a root by the intermediate value theorem and at most one by strict
monotonicity (the derivative's sign on the interval, by `nlinarith`). Eigenvalues of explicit matrices go through the
characteristic polynomial.
"""

from collections.abc import Sequence

from sage.all import AA, QQ, PolynomialRing, RealIntervalField, factorial, matrix
from sage.matrix.matrix0 import Matrix
from sage.rings.polynomial.polynomial_element import Polynomial

from veriphy.core import CertificateError
from veriphy.toolkit._lean import Lean, tactic

RIF = RealIntervalField(256)
SUPPORTED = ('exp', 'log', 'sin', 'cos', 'pi')
# mathlib's decimal bounds on π and e: (lemma, value), lower then upper
PI_LOWER = [
    ('Real.pi_gt_three', QQ(3)),
    ('Real.pi_gt_d2', QQ(314) / 100),
    ('Real.pi_gt_d4', QQ(31415) / 10000),
    ('Real.pi_gt_d6', QQ(3141592) / 1000000),
    ('Real.pi_gt_d20', QQ(314159265358979323846) / 10**20),
]
PI_UPPER = [
    ('Real.pi_lt_d2', QQ(315) / 100),
    ('Real.pi_lt_d4', QQ(31416) / 10000),
    ('Real.pi_lt_d6', QQ(3141593) / 1000000),
    ('Real.pi_lt_d20', QQ(314159265358979323847) / 10**20),
]
E_LOWER = [('Real.exp_one_gt_d9', QQ(27182818283) / 10**10)]
E_UPPER = [('Real.exp_one_lt_d9', QQ(27182818286) / 10**10)]
MAX_ORDER = 60
# the logarithm's series around 1 converges for 0 < x < LOG_RADIUS
LOG_RADIUS = 2


def _value(function: str, point: QQ) -> object:
    """Return an interval enclosing `function(point)`."""
    x = RIF(point)
    return {'exp': x.exp(), 'log': x.log(), 'sin': x.sin(), 'cos': x.cos(), 'pi': RIF.pi()}[function]


def _decimal(q: QQ) -> str:
    """Return a rational as Lean text."""
    q = QQ(q)
    return f'({q} : ℝ)' if q.denominator() == 1 else f'({q.numerator()} / {q.denominator()} : ℝ)'


def _from_table(table: Sequence[tuple[str, QQ]], bound: QQ, *, upper: bool) -> Lean | None:
    """Return `lt_trans` from a mathlib decimal lemma that implies the bound, or `None`."""
    for lemma, value in table:
        if (upper and value <= bound) or (not upper and value >= bound):
            return Lean(f'lt_trans {lemma} (by norm_num)' if upper else f'lt_trans (by norm_num) {lemma}', 'term')
    return None


def _series_order(function: str, point: QQ, bound: QQ, *, upper: bool) -> int:
    """Return the least truncation order whose remainder bound proves the bound, by interval arithmetic."""
    value = _value(function, point)
    gap = (RIF(bound) - value) if upper else (value - RIF(bound))
    if gap.lower() <= 0:
        message = f'the bound fails or is too tight: {function}({point}) ∈ {value.str(style="brackets")}'
        raise CertificateError(message)
    x = abs(RIF(point if function != 'log' else 1 - point))
    for n in range(1, MAX_ORDER):
        if function == 'exp':
            remainder = x**n * (n + 1) / (factorial(n) * n)
        elif function == 'log':
            remainder = x ** (n + 1) / (1 - x)
        else:
            break
        # the truncated sum is exact (rational); the remainder must fit in the gap
        if (2 * remainder).upper() < gap.lower():
            return n
    message = f'no truncation up to order {MAX_ORDER} proves the bound on {function}({point})'
    raise CertificateError(message)


def bound_proof(function: str, point: object, bound: object, *, upper: bool = True) -> Lean:
    """Return a proof of `f(point) < bound` (or `bound < f(point)` with `upper=False`).

    Args:
        function: `exp`, `log`, `sin`, `cos` or `pi` (the point is ignored for `pi`).
        point: A rational point (`|point| ≤ 1` for `exp`, `sin`, `cos`; `0 < point < 2` for `log`).
        bound: The rational bound.
        upper: Whether the bound is above the value.

    Returns:
        The tactic.

    Raises:
        CertificateError: If the function has no remainder bound in mathlib, the point is out of range, or the bound
            does not hold (with the enclosure Sage computed).

    Examples:
        >>> print(bound_proof('exp', 1, QQ(27183) / 10000))
        exact lt_trans Real.exp_one_lt_d9 (by norm_num)
        >>> try:
        ...     bound_proof('gamma', QQ(1) / 3, 3)
        ... except CertificateError as error:
        ...     print(str(error).split(';')[0])
        no remainder bound is available for gamma in mathlib
    """
    if function not in SUPPORTED:
        message = f'no remainder bound is available for {function} in mathlib; supported: {", ".join(SUPPORTED)}'
        raise CertificateError(message)
    point, bound = QQ(point), QQ(bound)
    value = _value(function, point)
    holds = (value < RIF(bound)) if upper else (value > RIF(bound))
    if not holds:
        message = f'the bound fails or is too tight: {function}({point}) ∈ {value.str(style="brackets")}'
        raise CertificateError(message)
    table = {'pi': (PI_UPPER if upper else PI_LOWER), 'exp': (E_UPPER if upper else E_LOWER) if point == 1 else []}
    direct = _from_table(table.get(function, []), bound, upper=upper)
    if direct is not None:
        return tactic(f'exact {direct}')
    side = 'h.2' if upper else 'h.1'
    if function == 'exp':
        if abs(point) > 1:
            message = 'the exponential series bound needs |x| ≤ 1; write exp x as a power of exp (x / m)'
            raise CertificateError(message)
        n = _series_order('exp', point, bound, upper=upper)
        lines = [
            f'have h := Real.exp_bound (x := {_decimal(point)}) (by norm_num [abs_le]) (n := {n}) (by norm_num)',
            'norm_num [Finset.sum_range_succ, Nat.factorial, abs_le] at h',
            f'linarith [{side}]',
        ]
    elif function == 'log':
        if not 0 < point < LOG_RADIUS:
            message = 'the logarithm series bound needs 0 < x < 2; use log (a * b) = log a + log b first'
            raise CertificateError(message)
        n = _series_order('log', point, bound, upper=upper)
        lines = [
            f'have h := Real.abs_log_sub_add_sum_range_le (x := 1 - {_decimal(point)}) (by norm_num [abs_lt]) {n}',
            'norm_num [Finset.sum_range_succ, abs_le] at h',
            f'linarith [{side}]',
        ]
    else:
        if abs(point) > 1:
            message = f'the {function} bound needs |x| ≤ 1'
            raise CertificateError(message)
        lemma = 'Real.sin_bound' if function == 'sin' else 'Real.cos_bound'
        lines = [
            f'have h := {lemma} (x := {_decimal(point)}) (by norm_num [abs_le])',
            'norm_num [abs_le] at h',
            f'linarith [{side}]',
        ]
    return tactic('\n'.join(lines))


def _critical_in(p: Polynomial, a: QQ, b: QQ) -> bool:
    """Return whether the derivative of `p` vanishes somewhere in `[a, b]` (exactly, over the algebraic reals)."""
    return any(a <= c <= b for c in p.derivative().roots(AA, multiplicities=False))


def isolate_roots(p: Polynomial) -> list[tuple[QQ, QQ]]:
    """Return disjoint rational intervals `(a, b)`, each holding exactly one simple real root of `p`.

    Args:
        p: A polynomial over ℚ.

    Returns:
        The intervals, with `p(a)` and `p(b)` nonzero and of opposite signs, and `p'` without a root in `[a, b]`.

    Examples:
        >>> x = PolynomialRing(QQ, 'x').gen()
        >>> isolate_roots(x**3 - 2*x - 1)[-1]
        (3/2, 3)
    """
    p = PolynomialRing(QQ, 'x')(p)
    intervals = []
    for root in p.roots(AA, multiplicities=False):
        a, b = QQ(root.interval_fast(RIF).lower().floor()) - 1, QQ(root.interval_fast(RIF).upper().ceil()) + 1
        while p(a) == 0 or p(b) == 0 or p(a) * p(b) > 0 or _critical_in(p, a, b):
            middle = (a + b) / 2
            if middle == root:
                middle = (a + middle) / 2
            a, b = (a, middle) if middle > root else (middle, b)
        intervals.append((a, b))
    return intervals


def root_proof(p_lean: str, a: object, b: object, p: Polynomial) -> Lean:
    """Return a proof of `∃! x : ℝ, (a < x ∧ x < b) ∧ p x = 0` for an interval from `isolate_roots`.

    Existence is the intermediate value theorem with the endpoint signs; uniqueness is strict monotonicity on
    `[a, b]`, from the derivative's sign, which `nlinarith` checks on the interval.

    Args:
        p_lean: The polynomial as the goal writes it, as a function of `x` (`x ^ 3 - 2 * x - 1`).
        a: The interval's left end.
        b: The interval's right end.
        p: The polynomial (Sage), to read the signs and the derivative.

    Returns:
        The tactic.

    Raises:
        CertificateError: If the signs at the ends agree, or `p'` vanishes in the interval.
    """
    a, b = QQ(a), QQ(b)
    p = PolynomialRing(QQ, 'x')(p)
    if p(a) * p(b) >= 0:
        message = f'p({a}) and p({b}) do not have opposite signs: no root is certified on the interval'
        raise CertificateError(message)
    if _critical_in(p, a, b):
        message = "p' vanishes in the interval: split it with isolate_roots"
        raise CertificateError(message)
    increasing = p(a) < 0
    mono = 'StrictMonoOn' if increasing else 'StrictAntiOn'
    of_deriv = 'strictMonoOn_of_deriv_pos' if increasing else 'strictAntiOn_of_deriv_neg'
    ivt = 'intermediate_value_Ioo' if increasing else 'intermediate_value_Ioo\''
    f = f'(fun x : ℝ => {p_lean})'
    derivative = str(p.derivative()).replace('^', ' ^ ').replace('*', ' * ')
    lines = [
        f'have hc : ContinuousOn {f} (Set.Icc {_decimal(a)} {_decimal(b)}) := by fun_prop',
        f'have hmono : {mono} {f} (Set.Icc {_decimal(a)} {_decimal(b)}) := by',
        f'  refine {of_deriv} (convex_Icc _ _) hc fun x hx => ?_',
        '  rw [interior_Icc] at hx',
        f'  have hd : deriv {f} x = {derivative} := by',
        '    simp (disch := fun_prop) [deriv_fun_sub, deriv_fun_add]',
        '    all_goals ring',
        '  rw [hd]; nlinarith [hx.1, hx.2, sq_nonneg x]',
        (
            f'obtain ⟨x, hx, hx0⟩ := {ivt} (by norm_num : {_decimal(a)} ≤ {_decimal(b)}) hc '
            '(by norm_num : (0 : ℝ) ∈ Set.Ioo _ _)'
        ),
        'refine ⟨x, ⟨hx, hx0⟩, fun y ⟨hy, hy0⟩ => ?_⟩',
        'exact hmono.injOn ⟨hy.1.le, hy.2.le⟩ ⟨hx.1.le, hx.2.le⟩ (hy0.trans hx0.symm)',
    ]
    return tactic('\n'.join(lines))


def characteristic_polynomial(m: Matrix) -> Polynomial:
    """Return `det(x I - M)` of a rational matrix, whose roots are its eigenvalues.

    Args:
        m: The matrix.

    Returns:
        The polynomial in `x`.
    """
    return matrix(QQ, m).charpoly('x')


def eigenvalue_proof(m: Matrix, matrix_lean: str, a: object, b: object) -> Lean:
    """Return a proof of `∃ x : ℝ, (a < x ∧ x < b) ∧ (x • 1 - M).det = 0`: an eigenvalue of a 3 by 3 matrix there.

    The determinant is expanded to the characteristic polynomial, whose root on the interval `root_proof` certifies.

    Args:
        m: The rational 3 by 3 matrix.
        matrix_lean: The matrix as the goal writes it (a literal over ℝ).
        a: The interval's left end (from `isolate_roots` on `characteristic_polynomial(m)`).
        b: The interval's right end.

    Returns:
        The tactic.

    Raises:
        CertificateError: If the matrix is not 3 by 3, or the interval does not isolate a simple root.
    """
    if (m.nrows(), m.ncols()) != (3, 3):  # the determinant expands by `Matrix.det_fin_three`
        message = 'eigenvalue certificates expand the determinant of 3 by 3 matrices'
        raise CertificateError(message)
    p = characteristic_polynomial(m)
    p_lean = str(p).replace('^', ' ^ ').replace('*', ' * ')
    root = '\n'.join(f'  {line}' for line in str(root_proof(p_lean, a, b, p)).splitlines())
    lines = [
        f'have hdet : ∀ x : ℝ, (x • (1 : Matrix (Fin 3) (Fin 3) ℝ) - {matrix_lean}).det = {p_lean} := by',
        '  intro x',
        '  simp [Matrix.det_fin_three, Matrix.one_apply]',
        '  ring',
        f'have hroot : ∃! x : ℝ, ({_decimal(QQ(a))} < x ∧ x < {_decimal(QQ(b))}) ∧ {p_lean} = 0 := by',
        root,
        'obtain ⟨x, hx, -⟩ := hroot',
        'exact ⟨x, hx.1, by rw [hdet]; exact hx.2⟩',
    ]
    return tactic('\n'.join(lines))
