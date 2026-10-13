"""Exact number fields for certificates: ℚ(√d), cyclotomic fields and ℚ(α), rendered for Lean with their generators.

Sage computes in the field; Lean sees the generator as a term (`Real.sqrt 2`, a primitive root `ζ`, a parameter `α`)
with the polynomial relation it satisfies. An identity is proved by normalizing (`ring_nf`), rewriting each power of
the generator at or above the relation's degree by its reduced form (each such fact proved by `linear_combination`
from the relation), and normalizing again: the reduced form of an element is unique, so a true identity closes.
"""

from dataclasses import dataclass

from sage.all import QQ, PolynomialRing, factor
from sage.matrix.matrix0 import Matrix
from sage.rings.polynomial.polynomial_element import Polynomial

from veriphy.core import CertificateError
from veriphy.toolkit._lean import Lean, tactic, term

X = PolynomialRing(QQ, 'x').gen()

# the entries of products, sums and literals of explicit matrices, evaluated without touching the field's generator
ENTRY_SIMP = (
    'set_option linter.unusedSimpArgs false in\n'
    'simp only [Matrix.mul_apply, Fin.sum_univ_succ, Fin.sum_univ_zero, Matrix.of_apply, Matrix.cons_val\', '
    'Matrix.cons_val_zero, Matrix.cons_val_one, Matrix.cons_val_succ, Matrix.head_cons, Matrix.empty_val\', '
    'Matrix.cons_val_fin_one, Matrix.one_apply, Matrix.zero_apply, Matrix.add_apply, Matrix.sub_apply, '
    'Matrix.neg_apply, Matrix.smul_apply, smul_eq_mul, Fin.isValue, Fin.reduceFinMk, Fin.zero_eta, Fin.mk_one, '
    'Fin.succ_zero_eq_one, Fin.reduceEq, ↓reduceIte, add_zero, Matrix.cons_val]'
)


@dataclass(frozen=True)
class FieldContext:
    """How a field's generator appears in Lean.

    Args:
        generator: The generator's Lean text, such as `Real.sqrt 2`, `ζ` or `α`.
        modulus: Its minimal polynomial over ℚ, in `x`; `None` for a transcendental parameter.
        fact: The name of the Lean fact `modulus(generator) = 0` (or `Real.sqrt d ^ 2 = d`), when there is one.
        setup: The tactic establishing the fact, or nothing when the goal's hypotheses already state it.
    """

    generator: str
    modulus: Polynomial | None
    fact: str | None
    setup: Lean | None


def _rational(q: object) -> str:
    """Return a rational coefficient's Lean text."""
    value = QQ(q)
    return str(value) if value.denominator() == 1 else f'({value.numerator()} / {value.denominator()})'


def render_polynomial(p: Polynomial, generator: str) -> str:
    """Return a polynomial over ℚ in `x` as Lean text in the generator, highest degree first.

    Args:
        p: The polynomial.
        generator: The generator's Lean text.

    Returns:
        The text, `0` for the zero polynomial.

    Examples:
        >>> render_polynomial(X**4 + X**3 - X / 2 + 1, 'ζ')
        'ζ ^ 4 + ζ ^ 3 - (1 / 2) * ζ + 1'
        >>> render_polynomial(-X, 'Real.sqrt 2')
        '-(Real.sqrt 2)'
    """
    g = generator if ' ' not in generator else f'({generator})'
    text = ''
    for k in sorted(p.exponents(), reverse=True):
        c = QQ(p[k])
        monomial = '' if k == 0 else (g if k == 1 else f'{g} ^ {k}')
        size = abs(c)
        if not monomial:
            body = _rational(size)
        elif size == 1:
            body = monomial
        else:
            body = f'{_rational(size)} * {monomial}'
        sign = '-' if c < 0 else '+'
        text = f'{text} {sign} {body}' if text else (f'-{body}' if c < 0 else body)
    return text or '0'


def quadratic_context(d: int, name: str = 'hs') -> FieldContext:
    """Return ℚ(√d) inside ℝ: the generator `Real.sqrt d`, with `Real.sqrt d ^ 2 = d` from `Real.sq_sqrt`.

    Args:
        d: A positive integer that is not a square.
        name: The fact's name.

    Returns:
        The context.

    Raises:
        CertificateError: If `d` is not a positive non-square integer.

    Examples:
        >>> print(quadratic_context(2).setup)
        have hs : Real.sqrt 2 ^ 2 = 2 := Real.sq_sqrt (by norm_num)
    """
    if QQ(d) <= 0 or QQ(d).denominator() != 1 or QQ(d).is_square():
        message = f'ℚ(√d) needs a positive non-square integer d, got {d}'
        raise CertificateError(message)
    generator = f'Real.sqrt {d}'
    return FieldContext(
        generator,
        X**2 - d,
        name,
        tactic(f'have {name} : {generator} ^ 2 = {d} := Real.sq_sqrt (by norm_num)'),
    )


def cyclotomic_context(n: int, zeta: str = 'ζ', primitive: str = 'hζ', name: str = 'hΦ') -> FieldContext:
    """Return ℚ(ζₙ) for a primitive root `ζ` with `primitive : IsPrimitiveRoot ζ n` among the hypotheses.

    The fact `Φₙ(ζ) = 0` is derived from mathlib's `IsPrimitiveRoot.isRoot_cyclotomic` and, for a prime power `n`,
    the explicit `Polynomial.cyclotomic_prime_pow_eq_geom_sum`. For other `n`, state `Φₙ(ζ) = 0` as a hypothesis
    named `name` and pass `primitive=None`.

    Args:
        n: The order of the root.
        zeta: The root's Lean text.
        primitive: The name of the hypothesis `IsPrimitiveRoot ζ n`, or `None` when the goal states `Φₙ(ζ) = 0`.
        name: The name of the fact `Φₙ(ζ) = 0`.

    Returns:
        The context.

    Raises:
        CertificateError: If `n` is not a prime power and no hypothesis states the relation.

    Examples:
        >>> print(cyclotomic_context(16).modulus)
        x^8 + 1
    """
    modulus = PolynomialRing(QQ, 'x').cyclotomic_polynomial(n)
    if primitive is None:
        return FieldContext(zeta, modulus, name, None)
    factored = factor(n)
    if len(factored) != 1:
        message = f'Φ_{n}(ζ) = 0 follows from IsPrimitiveRoot only for prime powers; state it as a hypothesis {name}'
        raise CertificateError(message)
    p, k = factored[0]
    setup = '\n'.join(
        [
            f'have {name} : {render_polynomial(modulus, zeta)} = 0 := by',
            f'  have h := {primitive}.isRoot_cyclotomic (by norm_num)',
            f'  rw [show ({n} : ℕ) = {p} ^ ({k - 1} + 1) by norm_num,',
            '    Polynomial.cyclotomic_prime_pow_eq_geom_sum (by decide)] at h',
            '  simp only [Polynomial.IsRoot, Polynomial.eval_finsetSum, Polynomial.eval_pow, Polynomial.eval_X,',
            '    Polynomial.eval_add, Polynomial.eval_one, Polynomial.eval_zero, Finset.sum_range_succ,',
            '    Finset.sum_range_zero, pow_zero, pow_one] at h',
            '  linear_combination h',
        ],
    )
    return FieldContext(zeta, modulus, name, tactic(setup))


def parameter_context(name: str = 'α') -> FieldContext:
    """Return ℚ(α) for a transcendental parameter `α`: identities are identities of rational functions.

    Args:
        name: The parameter's Lean text.

    Returns:
        The context; denominators need `≠ 0` hypotheses, which `field_simp` uses.
    """
    return FieldContext(name, None, None, None)


def lift(x: object) -> Polynomial:
    """Return the representative of a number-field element as a polynomial over ℚ in `x`.

    Args:
        x: An element of a number field with one generator, or a rational.

    Returns:
        The polynomial of degree below the field's degree.

    Examples:
        >>> from sage.all import QuadraticField
        >>> lift(QuadraticField(2, 's').gen() / 2 + 1)
        1/2*x + 1
    """
    if x in QQ:
        return X.parent()(QQ(x))
    return X.parent()(list(x.polynomial()))


def render_element(x: object, context: FieldContext) -> str:
    """Return a field element as Lean text in the context's generator (a rational function for a parameter).

    Args:
        x: An element of the field (a rational function in the parameter for ℚ(α)).
        context: The field's context.

    Returns:
        The text.

    Examples:
        >>> from sage.all import QuadraticField
        >>> render_element(QuadraticField(2, 's').gen() / 2, quadratic_context(2))
        '(1 / 2) * (Real.sqrt 2)'
    """
    if context.modulus is None:
        numerator, denominator = x.numerator(), x.denominator()
        top = render_polynomial(X.parent()(list(numerator)), context.generator)
        if denominator == 1:
            return top
        return f'({top}) / ({render_polynomial(X.parent()(list(denominator)), context.generator)})'
    return render_polynomial(lift(x), context.generator)


def field_matrix_term(m: Matrix, context: FieldContext) -> Lean:
    """Render a matrix over the field as a Lean `!![…]` literal.

    Args:
        m: The matrix.
        context: The field's context.

    Returns:
        The term.
    """
    rows = '; '.join(', '.join(render_element(x, context) for x in row) for row in m.rows())
    return term(f'!![{rows}]')


def _reductions(context: FieldContext, max_power: int) -> str:
    """Return `show g ^ k = r(g) by linear_combination q(g) * h` for `k` from the degree to `max_power`."""
    modulus = context.modulus
    if modulus is None or context.fact is None:
        return ''
    degree = modulus.degree()
    shows = []
    for k in range(degree, max_power + 1):
        quotient, remainder = (X**k).quo_rem(modulus)
        lhs = render_polynomial(X**k, context.generator)
        rhs = render_polynomial(remainder, context.generator)
        quotient_text = render_polynomial(quotient, context.generator)
        shows.append(f'show {lhs} = {rhs} by linear_combination ({quotient_text}) * {context.fact}')
    return ', '.join(shows)


def field_reduce(context: FieldContext, max_power: int | None = None) -> Lean:
    """Return a tactic closing a true identity over the field: normalize, reduce the generator's powers, normalize.

    Args:
        context: The field's context, whose fact is in scope.
        max_power: The largest power of the generator the normalized goal can contain (twice the degree minus two
            for a product of two reduced elements, the default).

    Returns:
        The tactic.

    Examples:
        >>> reduce = str(field_reduce(quadratic_context(2)))
        >>> reduce.startswith('(try ring_nf) <;> (set_option linter.unusedSimpArgs false in try simp only [show (')
        True
        >>> reduce.endswith('^ 2 = 2 by linear_combination (1) * hs]) <;> ring_nf')
        True
    """
    if context.modulus is None:
        return tactic('(try field_simp) <;> ring')
    bound = max_power if max_power is not None else 2 * context.modulus.degree() - 2
    reductions = _reductions(context, bound)
    if not reductions:
        return tactic('ring_nf')
    return tactic(
        f'(try ring_nf) <;> (set_option linter.unusedSimpArgs false in try simp only [{reductions}]) <;> ring_nf',
    )


def field_identity(context: FieldContext, max_power: int | None = None) -> Lean:
    """Return a proof of a scalar identity over the field: the generator's fact, then `field_reduce`.

    Args:
        context: The field's context.
        max_power: The largest power of the generator after normalizing the goal.

    Returns:
        The tactic.
    """
    steps = [str(context.setup)] if context.setup is not None else []
    steps.append(str(field_reduce(context, max_power)))
    return tactic('\n'.join(steps))


def field_matrix_identity(context: FieldContext, max_power: int | None = None) -> Lean:
    """Return an entrywise proof of an identity between explicit matrices over the field (`A * B = C`, `A = B`, …).

    Args:
        context: The field's context.
        max_power: The largest power of the generator in a normalized entry (by default that of a product of two
            reduced elements, enough for `A * B = C`).

    Returns:
        The tactic.
    """
    steps = [str(context.setup)] if context.setup is not None else []
    reduce = str(field_reduce(context, max_power))
    steps += ['ext i j', 'fin_cases i <;> fin_cases j', f'all_goals ({ENTRY_SIMP})', f'all_goals ({reduce})']
    return tactic('\n'.join(steps))


def check_matrix_identity(lhs: Matrix, rhs: Matrix) -> None:
    """Check in Sage that two matrices over a field agree, before Lean does.

    Args:
        lhs: The left side.
        rhs: The right side.

    Raises:
        CertificateError: If they differ, showing the difference.
    """
    if lhs != rhs:
        message = f'the identity fails in Sage; the difference is\n{lhs - rhs}'
        raise CertificateError(message)
