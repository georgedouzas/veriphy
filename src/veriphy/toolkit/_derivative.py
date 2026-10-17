"""Build Lean `HasDerivAt` proof terms from Sage expressions, by composing mathlib's derivative lemmas."""

import operator
from collections.abc import Mapping, Sequence

from sage.all import QQ, SR
from sage.symbolic.expression import Expression
from sage.symbolic.operators import add_vararg, mul_vararg

from veriphy.core import CertificateError
from veriphy.toolkit._lean import Lean, term
from veriphy.toolkit._problem import Problem
from veriphy.toolkit._symbolic_emit import symbolic

FUNCTION_LEMMAS = {'exp': 'exp', 'sin': 'sin', 'cos': 'cos'}
NONZERO_LEMMAS = {'log': 'log'}
POINTWISE = ('add', 'mul', 'div', 'pow')
APPLYING = ('mul', 'div', 'pow', 'sqrt', 'rpow_const', 'exp', 'sin', 'cos', 'log')
PI_LEMMAS = {'add': 'Pi.add_apply', 'mul': 'Pi.mul_apply', 'div': 'Pi.div_apply', 'pow': 'Pi.pow_apply'}
CLOSE = (
    'first | ring1 | (ring_nf; done) | (field_simp; done) | (field_simp; ring1) | (field_simp; ring_nf; done)'
    ' | (norm_num; done)'
)


class _Builder:
    """Compose a derivative proof term for expressions in one variable at one point.

    Args:
        var: The variable of differentiation.
        point: The point, an expression over the problem's atoms.
        problem: The problem whose atoms name the variables.
        proofs: Tactics proving side conditions no hypothesis states, by their Lean text.
    """

    def __init__(self, var: Expression, point: Expression, problem: Problem, proofs: Mapping[str, str]) -> None:
        self.var = var
        self.point = point
        self.problem = problem
        self.proofs = proofs
        self.point_text = self._text(point)
        self.pi_lemmas: set[str] = set()

    def _text(self, e: Expression) -> str:
        """Return the Lean text of an expression over the atoms, parenthesized as an argument."""
        text = str(symbolic(e, self.problem, lean_type='ℝ'))
        return text if text.startswith('(') else f'({text})'

    def _nonzero(self, e: Expression) -> str:
        """Return a proof of `e(point) ≠ 0`: a stated hypothesis, a supplied tactic, or fail naming the condition."""
        condition = f'{symbolic(e.subs({self.var: self.point}), self.problem, lean_type="")} ≠ 0'
        stated = {h.text: h.name for h in self.problem.hyps if h.name}
        stated.update({c.text: c.discharged_by for c in self.problem.domain if c.discharged_by})
        if condition in self.proofs:
            return f'(by {self.proofs[condition]})'
        if condition in stated:
            return str(stated[condition])
        message = f"the derivative needs '{condition}', which no hypothesis states; pass its proof"
        raise CertificateError(message)

    def build(self, e: Expression) -> str:
        """Return a proof term of `HasDerivAt (fun var => e) _ point`."""
        if not e.has(self.var):
            return f'(hasDerivAt_const {self.point_text} {self._text(e)})'
        if e.is_symbol():
            return f"(hasDerivAt_id' {self.point_text})"
        op, args = e.operator(), e.operands()
        if op == add_vararg:
            return self._fold(args, 'add')
        if op == mul_vararg:
            return self._product(args)
        if op == operator.pow:
            return self._power(args[0], args[1])
        return self._function(op.name() if hasattr(op, 'name') else str(op), args)

    def _operand(self, e: Expression) -> str:
        """Return the term of an operand that its parent applies to the point, noting the `Pi` lemmas it then needs."""
        self._note_applied(e)
        return self.build(e)

    def _note_applied(self, e: Expression) -> None:
        """Note the `Pi` lemma of a pointwise node applied to the point; its pointwise children are then applied too."""
        kind = _combinator(e, self.var)
        if kind is None:
            return
        self.pi_lemmas.add(PI_LEMMAS[kind])
        children = [e.operands()[0]] if kind == 'pow' else [a for a in e.operands() if a.has(self.var)]
        for child in children:
            self._note_applied(child**-1 if _is_reciprocal(child) else child)

    def _fold(self, args: Sequence[Expression], lemma: str) -> str:
        """Return the composition of the operands' terms by `HasDerivAt.add` (or `.mul`)."""
        applying = lemma in APPLYING
        term_of = self._operand if applying else self.build
        built = term_of(args[0])
        for i, a in enumerate(args[1:]):
            if applying and i > 0:
                self.pi_lemmas.add(PI_LEMMAS[lemma])  # the product so far is itself an applied pointwise operand
            built = f'({built}.{lemma} {term_of(a)})'
        return built

    def _product(self, args: Sequence[Expression]) -> str:
        """Return a product's term: a constant factor by `.const_mul`, a denominator by `.div`."""
        constant = [a for a in args if not a.has(self.var)]
        varying = [a for a in args if a.has(self.var)]
        numerator = [a for a in varying if not _is_reciprocal(a)]
        denominator = [a**-1 for a in varying if _is_reciprocal(a)]
        built = self._fold(numerator, 'mul') if numerator else f'(hasDerivAt_const {self.point_text} (1 : ℝ))'
        if denominator:
            below = SR(1).mul(*denominator) if len(denominator) > 1 else denominator[0]
            built = f'({built}.div {self._operand(below)} {self._nonzero(below)})'
        if constant:
            factor = SR(1).mul(*constant) if len(constant) > 1 else constant[0]
            built = f'({built}.const_mul {self._text(factor)})'
        return built

    def _power(self, base: Expression, exponent: Expression) -> str:
        """Return a power's term: `.pow n` for a natural exponent, `.sqrt` for 1/2, `.rpow_const` otherwise."""
        inner = self._operand(base)
        if exponent.has(self.var):
            message = f'the exponent of {base}^{exponent} depends on the variable; rewrite it with exp and log'
            raise CertificateError(message)
        if exponent.is_numeric() and exponent in QQ and QQ(exponent).denominator() == 1 and QQ(exponent) >= 0:
            return f'({inner}.pow {QQ(exponent)})'
        if exponent.is_numeric() and exponent in QQ and QQ(exponent) == QQ(1) / 2:
            return f'({inner}.sqrt {self._nonzero(base)})'
        return f'({inner}.rpow_const (Or.inl {self._nonzero(base)}))'

    def _function(self, name: str, args: Sequence[Expression]) -> str:
        """Return the term of a function of the variable: `.exp`, `.sin`, `.cos`, or `.log` with its condition."""
        if name in FUNCTION_LEMMAS:
            return f'({self._operand(args[0])}.{FUNCTION_LEMMAS[name]})'
        if name in NONZERO_LEMMAS:
            return f'({self._operand(args[0])}.{NONZERO_LEMMAS[name]} {self._nonzero(args[0])})'
        known = sorted({*FUNCTION_LEMMAS, *NONZERO_LEMMAS, 'sqrt', 'powers'})
        message = f"no derivative lemma for '{name}' (known: {', '.join(known)})"
        raise CertificateError(message)


def _combinator(e: Expression, var: Expression) -> str | None:
    """Return the pointwise combinator (`add`, `mul`, `div`, `pow`) whose term `e` gets, `None` for a lambda."""
    if not e.has(var) or e.is_symbol():
        return None
    op = e.operator()
    if op == add_vararg:
        return 'add'
    if op == mul_vararg:
        varying = [a for a in e.operands() if a.has(var)]
        if any(_is_reciprocal(a) for a in varying):
            return 'div'
        return 'mul' if len(varying) > 1 else None
    if op == operator.pow:
        exponent = e.operands()[1]
        natural = exponent.is_numeric() and exponent in QQ and QQ(exponent) >= 0 and QQ(exponent).denominator() == 1
        return 'pow' if natural else None
    return None


def _pointwise_lemmas(e: Expression, var: Expression) -> set[str]:
    """Return the `Pi` lemmas that unfold the pointwise operations of the function a term for `e` proves."""
    kind = _combinator(e, var)
    if kind is None:
        return set()
    children = [e.operands()[0]] if kind == 'pow' else [a for a in e.operands() if a.has(var)]
    found = {PI_LEMMAS[kind]}
    for child in children:
        found |= _pointwise_lemmas(child**-1 if _is_reciprocal(child) else child, var)
    return found


def _is_reciprocal(e: Expression) -> bool:
    """Return whether `e` is a power with a negative numeral exponent, a factor of a denominator."""
    if e.operator() != operator.pow:
        return False
    exponent = e.operands()[1]
    return bool(exponent.is_numeric() and exponent in QQ and QQ(exponent) < 0)


def has_deriv_at(
    expr: object,
    var: Expression,
    point: object,
    problem: Problem,
    proofs: Mapping[str, str] | None = None,
) -> Lean:
    """Build a proof term of `HasDerivAt (fun var => expr) _ point` from mathlib's derivative lemmas.

    The term composes `hasDerivAt_const`, `hasDerivAt_id'`, `.add`, `.mul`, `.div`, `.const_mul`, `.pow`, `.sqrt`,
    `.rpow_const`, `.exp`, `.log`, `.sin` and `.cos`. The derivative it proves is mathlib's unsimplified form, which
    a proof states as Sage's derivative by `HasDerivAt.congr_deriv` and `ring_nf` or `field_simp`. A quotient, `log`,
    `sqrt` or real power needs its argument nonzero at the point: a hypothesis stating it, or a tactic in `proofs`.
    Any other variable of the expression is a constant, so the same term proves partial derivatives.

    Args:
        expr: The function's body, an expression in `var` and the problem's atoms.
        var: The variable of differentiation, a Sage symbol.
        point: The point, an expression over the problem's atoms.
        problem: The problem whose atoms name the variables.
        proofs: Tactics proving side conditions no hypothesis states, by their Lean text.

    A side condition neither stated nor supplied, or a function with no derivative lemma, raises `CertificateError`
    naming it.

    Returns:
        The proof term.

    Examples:
        >>> from sage.all import exp, log
        >>> from veriphy.toolkit import read_problem
        >>> prob = read_problem({'vars': ['x0'], 'atoms': ['a'], 'goal': {'kind': 'false'}})
        >>> t = SR.var('t')
        >>> str(has_deriv_at(t**2 * exp(t), t, 1, prob))
        "(((hasDerivAt_id' (1 : ℝ)).pow 2).mul ((hasDerivAt_id' (1 : ℝ)).exp))"
        >>> has_deriv_at(log(t), t, prob.symbols['x0'], prob)
        Traceback (most recent call last):
        ...
        veriphy.core._errors.CertificateError: the derivative needs 'a ≠ 0', which no hypothesis states; pass its proof
    """
    builder = _Builder(var, SR(point), problem, proofs or {})
    built = builder.build(SR(expr))
    return term(built)


def has_deriv_at_proof(
    expr: object,
    var: Expression,
    point: object,
    value: object,
    problem: Problem,
    *,
    proofs: Mapping[str, str] | None = None,
    name: str = 'hd',
    function: str | None = None,
    at: str | None = None,
) -> Lean:
    """Build `have name : HasDerivAt (fun var => expr) value point`, proved from the composed term.

    The step converts the term of `has_deriv_at` to the stated derivative (Sage's), unfolds the pointwise operations
    the term introduced, and closes the algebra by `ring` or `field_simp`. `name.deriv` then rewrites `deriv`.

    Args:
        expr: The function's body, an expression in `var` and the problem's atoms.
        var: The variable of differentiation; a symbol ending in `_` renders without it (`t_` as `t`).
        point: The point, an expression over the problem's atoms.
        value: The derivative at the point, as Sage computed it.
        problem: The problem whose atoms name the variables.
        proofs: Tactics proving side conditions no hypothesis states, by their Lean text.
        name: The name of the fact.
        function: The function's Lean text, stated instead of the rendered body (so it matches a goal's `deriv`).
        at: The point's Lean text, stated instead of the rendered point.

    Returns:
        The tactic block.

    Examples:
        >>> from sage.all import exp
        >>> from veriphy.toolkit import read_problem
        >>> prob = read_problem({'vars': ['x0'], 'atoms': ['a'], 'carrier': 'ℝ', 'goal': {'kind': 'false'}})
        >>> t = SR.var('t_')
        >>> first, second, closing = str(has_deriv_at_proof(t**2 * exp(t), t, 1, 3 * exp(1), prob)).splitlines()
        >>> print(first); print(second)
        have hd : HasDerivAt (fun t => ((t ^ 2) * (Real.exp t) : ℝ)) ((3 * (Real.exp 1) : ℝ)) (1 : ℝ) := by
          convert (((hasDerivAt_id' (1 : ℝ)).pow 2).mul ((hasDerivAt_id' (1 : ℝ)).exp)) using 1
        >>> closing.split(' | (simp only')[0]
        '  all_goals first | rfl | (funext y; simp only [Pi.mul_apply, Pi.pow_apply]; ring_nf; done)'
    """
    builder = _Builder(var, SR(point), problem, proofs or {})
    built = builder.build(SR(expr))
    stated_function = function or f'fun {str(var).rstrip("_")} => {symbolic(SR(expr), problem, lean_type="ℝ")}'
    stated_point = f'({at})' if at else builder.point_text
    stated_value = symbolic(SR(value), problem, lean_type='ℝ')
    lines = [
        f'have {name} : HasDerivAt ({stated_function}) ({stated_value}) {stated_point} := by',
        f'  convert {built} using 1',
    ]
    applied = ', '.join(sorted(builder.pi_lemmas))
    value_close = f'(simp only [{applied}]; {CLOSE})' if applied else f'({CLOSE})'
    # `convert` may leave the function too, when the stated text orders arguments as Sage does (`s * ω`)
    unfold = ', '.join(sorted(_pointwise_lemmas(SR(expr), var)))
    function_close = f'(funext y; simp only [{unfold}]; ring_nf; done)' if unfold else '(funext y; ring_nf; done)'
    lines.append(f'  all_goals first | rfl | {function_close} | {value_close}')
    return Lean('\n'.join(lines), 'tactic')
