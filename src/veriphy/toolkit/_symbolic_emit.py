"""Render Sage symbolic expressions and matrices as Lean terms, and build domain-aware steps over them.

Functions and constants render through the problem's translation tables (core first, after LeanSage's
`ExprToAST.lean`); `abs` renders as `|·|` of the argument's own type.
"""

import operator
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from sage.all import QQ, SR, I
from sage.matrix.matrix0 import Matrix
from sage.symbolic.expression import Expression
from sage.symbolic.operators import FDerivativeOperator, add_vararg, mul_vararg

from veriphy.core import CertificateError
from veriphy.toolkit._emit import field_simp, fresh_name, steps
from veriphy.toolkit._lean import Lean, leaving_goals, parenthesize, rational, tactic, term
from veriphy.toolkit._problem import DOMAIN_KINDS, Condition, MatrixIndex, Problem, parse_symbolic

STRUCTURAL = ('abs', 'mod')
INTEGER_OPERATORS = ('factorial', 'binomial', 'gcd', 'mod', 'floor', 'ceil')
INTEGER_RESULT = ('floor', 'ceil')
INTEGER_TYPES = ('ℕ', 'ℤ')
WILDCARDS = 4


@dataclass(frozen=True)
class _Context:
    """Hold what rendering a sub-expression needs: the problem, and the Lean type the text must have (empty: any)."""

    problem: Problem
    lean_type: str

    def at(self, lean_type: str) -> '_Context':
        """Return the same context at another type."""
        return _Context(self.problem, lean_type)


def _is_complex(e: Expression, problem: Problem) -> bool:
    """Return whether `e` lives in ℂ: it mentions `I` or an atom of type ℂ."""
    if e.has(I):
        return True
    return any(problem.atom_types.get(str(v)) == 'ℂ' for v in e.variables())


def _looks_negative(e: Expression) -> bool:
    """Return whether `e` is a negative rational or a product with a negative rational coefficient."""
    if e.is_numeric():
        return e in QQ and QQ(e) < 0
    if e.operator() == mul_vararg:
        return any(o.is_numeric() and o in QQ and QQ(o) < 0 for o in e.operands())
    return False


def _function(name: str, e: Expression, problem: Problem) -> str:
    """Return the Lean name of a table function applied to `e`, dispatching on `e`'s type (ℂ or ℝ)."""
    wanted = 'ℂ' if _is_complex(e, problem) else 'ℝ'
    integer = name in INTEGER_OPERATORS
    for table in problem.tables:
        for entry in table.functions:
            if entry.sage == name and (integer or not entry.types or wanted in entry.types):
                return entry.lean
    known = sorted({f.sage for t in problem.tables for f in t.functions} | set(STRUCTURAL))
    message = (
        f"no Lean rendering for the function '{name}' over {wanted} (known: {', '.join(known)}); "
        'add an entry to the project\'s .veriphy/translations/'
    )
    raise CertificateError(message)


def _constant(sage_name: str, problem: Problem) -> str | None:
    """Return the Lean name of a table constant, by its Sage name."""
    for table in problem.tables:
        for entry in table.constants:
            if entry.sage == sage_name:
                return entry.lean
    return None


def _cast(text: str, own: str, ctx: _Context) -> str:
    """Return `text`, computed at type `own`, cast to the context's type when the two differ."""
    if not ctx.lean_type or own == ctx.lean_type:
        return text
    return f'(({text} : {own}) : {ctx.lean_type})'


def _integer_type(e: Expression, problem: Problem) -> str:
    """Return ℕ when every atom of `e` is a natural number, ℤ otherwise."""
    return 'ℕ' if all(problem.atom_types.get(str(v)) == 'ℕ' for v in e.variables()) else 'ℤ'


def _check_integral(e: Expression, ctx: _Context) -> None:
    """Refuse a sub-expression that has no meaning at ℕ or ℤ: a fraction, or a subtraction at ℕ."""
    if ctx.lean_type not in INTEGER_TYPES:
        return
    if e.is_numeric() and e in QQ and (QQ(e).denominator() != 1 or (ctx.lean_type == 'ℕ' and QQ(e) < 0)):
        message = (
            f'{e} has no exact meaning at {ctx.lean_type}; render this expression at a field type (lean_type=\'ℚ\')'
        )
        raise CertificateError(message)
    if e.operator() == add_vararg and ctx.lean_type == 'ℕ' and any(_looks_negative(a) for a in e.operands()):
        message = f'{e} subtracts at ℕ, where Lean truncates; render it at ℤ or a field (lean_type=\'ℤ\')'
        raise CertificateError(message)


def _is_polynomial_type(lean_type: str | None) -> bool:
    """Return whether a Lean type is a polynomial ring (`ℚ[X]` or `Polynomial ℚ`)."""
    return lean_type is not None and (lean_type.endswith('[X]') or lean_type.startswith('Polynomial '))


def _render_leaf(e: Expression, ctx: _Context) -> str:
    """Return the Lean text of a symbol, number or constant."""
    if e.is_symbol():
        name = str(e)
        if name in ctx.problem.atoms:
            return parenthesize(ctx.problem.atoms[name])
        if name.endswith('_'):
            return name[:-1]
        ring = ctx.lean_type or ctx.problem.carrier
        if name == 'X' and _is_polynomial_type(ring):
            # the generator of the goal's polynomial ring
            return f'(Polynomial.X : {ring})'
        message = f"symbol '{name}' is not an atom of the problem"
        raise CertificateError(message)
    if e.is_numeric() and e in QQ:
        return str(rational(QQ(e)))
    constant = _constant('I' if e == I else str(e), ctx.problem)
    if constant is not None:
        return constant
    message = f'no Lean rendering for the constant {e}'
    raise CertificateError(message)


def _render_sum(args: Sequence[Expression], ctx: _Context) -> str:
    """Return a sum, writing terms with a negative coefficient as subtractions."""
    text = _render(args[0], ctx)
    for a in args[1:]:
        text += f' - {_operand(-a, ctx)}' if _looks_negative(a) else f' + {_operand(a, ctx)}'
    return text


def _recorded_type(e: Expression, problem: Problem) -> str | None:
    """Return the Lean type of `e` when Lean computes it at another type than its context (a `typed` marker)."""
    for sub, lean_type in problem.typed:
        if e.is_trivially_equal(sub):
            return lean_type
    return None


def _render(e: Expression, ctx: _Context) -> str:
    """Return the Lean text of a symbolic expression at the context's type."""
    _check_integral(e, ctx)
    recorded = _recorded_type(e, ctx.problem)
    if recorded is not None and recorded != ctx.lean_type:
        return _cast(_render(e, ctx.at(recorded)), recorded, ctx)
    op, args = e.operator(), e.operands()
    if op is None:
        return _render_leaf(e, ctx)
    renderers = {add_vararg: _render_sum, mul_vararg: _render_product}
    if op in renderers:
        return renderers[op](args, ctx)
    if op == operator.pow:
        return _render_power(args[0], args[1], ctx)
    return _render_operator(op, e, args, ctx)


def _render_operator(op: object, e: Expression, args: Sequence[Expression], ctx: _Context) -> str:
    """Return a function application: an unknown function or its derivative, an integer operator, or a table one."""
    if isinstance(op, FDerivativeOperator):
        return _render_derivative(op, args, ctx)
    name = op.name() if hasattr(op, 'name') else str(op)
    if name in ctx.problem.functions:
        return f'{ctx.problem.functions[name][0]} ' + ' '.join(_operand(a, ctx) for a in args)
    return _render_integer(name, e, args, ctx) if name in INTEGER_OPERATORS else _render_application(name, args, ctx)


def _render_derivative(op: FDerivativeOperator, args: Sequence[Expression], ctx: _Context) -> str:
    """Return a derivative of an unknown function of one variable: `deriv (deriv x) t`."""
    name = op.function().name()
    if name not in ctx.problem.functions or len(args) != 1:
        message = f'no Lean rendering for the derivative of {name}; only unknown functions of one variable render'
        raise CertificateError(message)
    text = ctx.problem.functions[name][0]
    for _ in op.parameter_set():
        text = f'deriv {parenthesize(text)}' if text != ctx.problem.functions[name][0] else f'deriv {text}'
    return f'{text} {_operand(args[0], ctx)}'


def _render_integer(name: str, e: Expression, args: Sequence[Expression], ctx: _Context) -> str:
    """Return an integer-valued operator at its own type (ℕ or ℤ), cast to the context's type."""
    own = 'ℤ' if name in INTEGER_RESULT else _integer_type(e, ctx.problem)
    inner = ctx.at(ctx.lean_type if name in INTEGER_RESULT else own)
    if name == 'mod':
        text = f'{_operand(args[0], inner)} % {_operand(args[1], inner)}'
    else:
        lean = _function(name, args[0], ctx.problem)
        text = f'{lean} ' + ' '.join(_operand(a, inner) for a in args)
    return _cast(text, own, ctx)


def _render_application(name: str, args: Sequence[Expression], ctx: _Context) -> str:
    """Return a function application: `|·|` or a table function."""
    if name == 'abs':
        return f'|{_render(args[0], ctx)}|'
    return f'{_function(name, args[0], ctx.problem)} ' + ' '.join(_operand(a, ctx) for a in args)


def _is_grouped(text: str) -> bool:
    """Return whether the whole text is one parenthesized group, such as a cast `((n : ℕ) : ℝ)`."""
    if not (text.startswith('(') and text.endswith(')')):
        return False
    depth = 0
    for i, char in enumerate(text):
        depth += {'(': 1, ')': -1}.get(char, 0)
        if depth == 0 and i < len(text) - 1:
            return False
    return True


def _operand(e: Expression, ctx: _Context) -> str:
    """Return the Lean text of `e`, parenthesized unless atomic or already one group."""
    text = _render(e, ctx)
    return text if _is_grouped(text) else parenthesize(text)


def _render_product(args: Sequence[Expression], ctx: _Context) -> str:
    """Return a product, with negative integer powers moved to a denominator."""
    numerator: list[str] = []
    denominator: list[str] = []
    sign = ''
    for a in args:
        if a.is_numeric() and a in QQ:
            q = QQ(a)
            sign = '-' if q < 0 else sign
            if abs(q).numerator() != 1:
                numerator.insert(0, str(abs(q).numerator()))
            if q.denominator() != 1:
                denominator.insert(0, str(q.denominator()))
        elif a.operator() == operator.pow and a.operands()[1].is_numeric() and a.operands()[1] < 0:
            denominator.append(_operand(a.operands()[0] ** -a.operands()[1], ctx))
        else:
            numerator.append(_operand(a, ctx))
    if denominator and ctx.lean_type in INTEGER_TYPES:
        message = f'a quotient has no exact meaning at {ctx.lean_type}; render this expression at a field type'
        raise CertificateError(message)
    text = ' * '.join(numerator) or '1'
    if denominator:
        text += ' / ' + (denominator[0] if len(denominator) == 1 else f'({" * ".join(denominator)})')
    return f'{sign}{text}'


def _render_power(base: Expression, exponent: Expression, ctx: _Context) -> str:
    """Return a power: `sqrt` for exponent 1/2, a reciprocal for negative integers, `^` otherwise."""
    if exponent.is_numeric() and exponent in QQ:
        q = QQ(exponent)
        if q == QQ(1) / 2:
            return f'{_function("sqrt", base, ctx.problem)} {_operand(base, ctx)}'
        if q.denominator() == 1:
            power = f'{_operand(base, ctx)} ^ {abs(q)}'
            return power if q >= 0 else f'1 / {power}'
        return f'{_operand(base, ctx)} ^ ({rational(q)} : ℝ)'
    return f'{_operand(base, ctx)} ^ {_operand(exponent, ctx)}'


def symbolic(expr: object, problem: Problem, lean_type: str | None = None) -> Lean:
    """Render a Sage symbolic expression over the problem's variables as a Lean term over its atoms.

    Functions render through the problem's translation tables, dispatching on type: `exp`, `log`, `sin`, `cos`,
    `tan` render as their `Complex` versions when the argument mentions `I` or a ℂ atom and as `Real` versions
    otherwise; `abs` renders as `|·|`, `pi` as `Real.pi`, `I` as `Complex.I`. The term is rendered at `lean_type` (the
    problem's carrier by default) and ascribed to it; integer-valued operators (`factorial`, `binomial`, `gcd`,
    remainders, `floor`, `ceil`) and sub-expressions Lean computes at ℕ or ℤ render at that type and are cast. A
    function outside the tables, a symbol that is not an atom, or a fraction or ℕ subtraction rendered at ℕ or ℤ
    raises `CertificateError`.

    Args:
        expr: A symbolic expression, or anything Sage's symbolic ring converts, over `problem.symbols`.
        problem: The problem whose atoms name the variables.
        lean_type: The Lean type of the term, the problem's carrier when `None`; empty for no ascription.

    Returns:
        The term.

    Examples:
        >>> from sage.all import exp, sqrt
        >>> from veriphy.toolkit import read_problem
        >>> prob = read_problem({'vars': ['x0', 'x1'], 'atoms': ['x', 'z'], 'atom_types': ['ℝ', 'ℂ'],
        ...     'goal': {'kind': 'false'}})
        >>> x0, x1 = prob.symbols['x0'], prob.symbols['x1']
        >>> str(symbolic(abs(x0 - 1), prob)), str(symbolic(exp(x1), prob)), str(symbolic(sqrt(x0) / (x0**2 + 1), prob))
        ('|x - 1|', 'Complex.exp z', '(Real.sqrt x) / (x ^ 2 + 1)')
        >>> nat = read_problem({'vars': ['x0', 'x1'], 'atoms': ['x', 'n'], 'atom_types': ['ℝ', 'ℕ'], 'carrier': 'ℝ',
        ...     'goal': {'expr': "(typed(mod(x1, 7), 'ℕ') + x0) - (x0)", 'kind': 'other', 'rel': 'le', 'text': ''}})
        >>> str(symbolic(nat.goal.expr + nat.symbols['x0'], nat))
        '(x + ((n % 7 : ℕ) : ℝ) : ℝ)'
        >>> str(symbolic(nat.symbols['x1'] + 1, nat, lean_type='ℕ'))
        '(n + 1 : ℕ)'
    """
    ctx = _Context(problem, problem.carrier if lean_type is None else lean_type)
    text = _render(SR(expr), ctx)
    ascribed = _is_grouped(text) and text.endswith(f' : {ctx.lean_type})')
    return term(f'({text} : {ctx.lean_type})' if ctx.lean_type and not ascribed else text)


def matrix_term(m: Matrix, problem: Problem, index: MatrixIndex | None = None) -> Lean:
    """Render a Sage matrix as a Lean `!![…]` literal over the problem's atoms, or by blocks for a sum index.

    Args:
        m: A Sage matrix with entries Sage's symbolic ring converts.
        problem: The problem whose atoms name the variables.
        index: The index type of a matrix indexed by `Fin a ⊕ Fin b` (from `problem.matrix_indices`): the matrix is
            rendered as `Matrix.fromBlocks` of its blocks, a term of that type.

    Returns:
        The term.

    Raises:
        CertificateError: If the matrix's size does not match the index type.

    Examples:
        >>> from veriphy.toolkit import read_problem
        >>> from sage.all import matrix
        >>> prob = read_problem({'vars': ['x0'], 'atoms': ['c'], 'goal': {'kind': 'false'}})
        >>> str(matrix_term(matrix(SR, [[1, prob.symbols['x0']], [0, 1/2]]), prob))
        '!![1, c; 0, 1 / 2]'
        >>> sum_index = MatrixIndex((1, 2), (1, 2), 'Matrix (Fin 1 ⊕ Fin 2) (Fin 1 ⊕ Fin 2) ℚ')
        >>> str(matrix_term(matrix(SR, [[1, 0, 0], [0, -1, 0], [0, 0, -1]]), prob, sum_index))
        '(Matrix.fromBlocks !![1] !![0, 0] !![0; 0] !![-1, 0; 0, -1] : Matrix (Fin 1 ⊕ Fin 2) (Fin 1 ⊕ Fin 2) ℚ)'
    """
    ctx = _Context(problem, '')

    def literal(block: Matrix) -> str:
        """Return the `!![…]` literal of a block."""
        rows = [', '.join(_render(SR(entry), ctx) for entry in row) for row in block.rows()]
        return '!![' + '; '.join(rows) + ']'

    if index is None:
        return term(literal(m))
    two_blocks = len(index.rows) == len(index.cols) == len(('inl', 'inr'))
    if not two_blocks or (m.nrows(), m.ncols()) != (sum(index.rows), sum(index.cols)):
        message = f'a {m.nrows()} by {m.ncols()} matrix does not split into the blocks of {index.text}'
        raise CertificateError(message)
    (r, _), (c, _) = index.rows, index.cols
    blocks = [m[:r, :c], m[:r, c:], m[r:, :c], m[r:, c:]]
    return term(f'(Matrix.fromBlocks {" ".join(literal(b) for b in blocks)} : {index.text})')


def require_domain(
    problem: Problem,
    kinds: Sequence[str] = DOMAIN_KINDS,
    proofs: Mapping[str, Lean | str] | None = None,
) -> tuple[list[str], list[Lean]]:
    """Discharge the problem's domain conditions of the given kinds, by hypothesis or by a supplied proof.

    Args:
        problem: The problem.
        kinds: The condition kinds required (`ne`, `nonneg`, `pos`).
        proofs: A tactic proving a condition, by the condition's text, for conditions no hypothesis discharges.

    Returns:
        The names of facts stating the conditions, and the `have` steps introducing the supplied proofs.

    Raises:
        CertificateError: If a required condition is neither discharged nor supplied, naming each one.

    Examples:
        >>> from veriphy.toolkit import read_problem
        >>> prob = read_problem({'vars': ['x0'], 'atoms': ['x'], 'goal': {'kind': 'false'},
        ...     'domain': [{'expr': 'x0', 'kind': 'pos', 'text': '0 < x'}]})
        >>> require_domain(prob)
        Traceback (most recent call last):
        ...
        veriphy.core._errors.CertificateError: undischarged domain conditions: 0 < x (pass their proofs)
        >>> names, haves = require_domain(prob, proofs={'0 < x': 'positivity'})
        >>> names, [str(h) for h in haves]
        (['hd'], ['have hd : 0 < x := by positivity'])
    """
    proofs = proofs or {}
    names: list[str] = []
    haves: list[Lean] = []
    missing: list[Condition] = []
    for c in problem.domain:
        if c.kind not in kinds:
            continue
        if c.text in proofs:
            name = fresh_name(problem, 'hd', names)
            names.append(name)
            haves.append(tactic(f'have {name} : {c.text} := by {proofs[c.text]}'))
        elif c.discharged_by:
            names.append(c.discharged_by)
        else:
            missing.append(c)
    if missing:
        listed = '; '.join(c.text for c in missing)
        message = f'undischarged domain conditions: {listed} (pass their proofs)'
        raise CertificateError(message)
    return names, haves


def field_simp_clearing(problem: Problem, proofs: Mapping[str, Lean | str] | None = None) -> Lean:
    """Clear the problem's denominators with `field_simp`, passing a fact for every nonzero-denominator condition.

    A denominator condition neither discharged nor supplied raises `CertificateError`, as in `require_domain`.

    Args:
        problem: The problem.
        proofs: A tactic proving a denominator condition no hypothesis discharges, by the condition's text.

    Returns:
        The tactic, preceded by a `have` per supplied proof.

    Examples:
        >>> from veriphy.toolkit import read_problem
        >>> prob = read_problem({'vars': ['x0', 'x1'], 'atoms': ['y', 'x'], 'goal': {'kind': 'false'},
        ...     'domain': [{'expr': 'x0', 'kind': 'ne', 'text': 'y ≠ 0', 'discharged_by': 'hy'},
        ...                {'expr': 'x1^2 + 1', 'kind': 'ne', 'text': 'x ^ 2 + 1 ≠ 0'}]})
        >>> print(field_simp_clearing(prob, proofs={'x ^ 2 + 1 ≠ 0': 'positivity'}))
        have hd : x ^ 2 + 1 ≠ 0 := by positivity
        field_simp [hy, hd]
    """
    names, haves = require_domain(problem, ('ne',), proofs)
    return steps(*haves, field_simp(names)) if haves else field_simp(names)


def lemma_rewrite(
    lemma: str,
    problem: Problem,
    *,
    reverse: bool = False,
    side: Sequence[str] = (),
    proofs: Mapping[str, Lean | str] | None = None,
    at: str | None = None,
) -> Lean:
    """Rewrite with a named mathlib lemma, passing its side conditions as arguments.

    Each side condition is the Lean text of a proposition. It is passed as the hypothesis or domain fact that states
    it, or as `(by <proof>)` from `proofs`.

    Args:
        lemma: The lemma name, such as `Real.exp_add`.
        problem: The problem.
        reverse: Rewrite right to left (`← lemma`).
        side: The lemma's side conditions, in argument order.
        proofs: A tactic proving a side condition no hypothesis states, by its text.
        at: A hypothesis to rewrite instead of the goal.

    Returns:
        The tactic.

    Raises:
        CertificateError: If a side condition is neither stated nor supplied, naming it.

    Examples:
        >>> from veriphy.toolkit import read_problem
        >>> prob = read_problem({'vars': ['x0'], 'atoms': ['u'], 'goal': {'kind': 'false'},
        ...     'hyps': [{'name': 'hu', 'poly': '-x0', 'rel': 'le', 'text': '0 ≤ u'}]})
        >>> str(lemma_rewrite('Real.exp_add', prob, reverse=True))
        'rw [← Real.exp_add]'
        >>> str(lemma_rewrite('Real.sqrt_mul_self', prob, side=['0 ≤ u'], at='h'))
        'rw [Real.sqrt_mul_self hu] at h'
        >>> lemma_rewrite('Real.log_exp', prob, side=['0 < u'])
        Traceback (most recent call last):
        ...
        veriphy.core._errors.CertificateError: side condition '0 < u' of Real.log_exp is not stated; pass its proof
    """
    proofs = proofs or {}
    stated = {h.text: h.name for h in problem.hyps if h.name}
    stated.update({c.text: c.discharged_by for c in problem.domain if c.discharged_by})
    args = []
    for condition in side:
        if condition in proofs:
            args.append(f'(by {proofs[condition]})')
        elif condition in stated:
            args.append(str(stated[condition]))
        else:
            message = f"side condition '{condition}' of {lemma} is not stated; pass its proof"
            raise CertificateError(message)
    rule = ' '.join([f'{"← " if reverse else ""}{lemma}', *args])
    return leaving_goals(tactic(f'rw [{rule}]' + (f' at {at}' if at else '')))


@dataclass(frozen=True)
class RewriteCandidate:
    """Hold a rewrite the problem's tables offer for its goal, with side conditions filled in where they could be.

    Args:
        lemma: The lemma name.
        reverse: Rewrite right to left.
        side: The side conditions as Lean text over the goal's atoms.
        namespace: The table the entry came from.
    """

    lemma: str
    reverse: bool
    side: tuple[str, ...]
    namespace: str

    def emit(self, problem: Problem, proofs: Mapping[str, Lean | str] | None = None, at: str | None = None) -> Lean:
        """Return the rewrite step, passing each side condition as `(by assumption)` or a supplied proof.

        Sage orders the arguments of a commutative pattern its own way, so a stated side condition is passed as
        `(by assumption)`, which Lean runs after unifying the lemma with the goal and which therefore finds the
        right hypothesis whatever the order.

        Args:
            problem: The problem.
            proofs: A tactic proving a side condition no hypothesis states, by its text.
            at: A hypothesis to rewrite instead of the goal.

        Returns:
            The tactic.

        Raises:
            CertificateError: If a side condition is neither stated nor supplied, naming it.
        """
        proofs = proofs or {}
        stated = {h.text for h in problem.hyps if h.name} | {c.text for c in problem.domain if c.discharged_by}
        args = []
        for condition in self.side:
            if condition in proofs:
                args.append(f'(by {proofs[condition]})')
            elif condition in stated:
                args.append('(by assumption)')
            else:
                message = f"side condition '{condition}' of {self.lemma} is not stated; pass its proof"
                raise CertificateError(message)
        rule = ' '.join([f'{"← " if self.reverse else ""}{self.lemma}', *args])
        return leaving_goals(tactic(f'rw [{rule}]' + (f' at {at}' if at else '')))


def _mentions(function: str, text: str) -> bool:
    """Return whether Lean text mentions a constant, by full name or by its last component."""
    tokens = set(re.findall(r"[\w.'₀-₉]+", text))
    short = {t.rsplit('.', 1)[-1] for t in tokens}
    return function in tokens or function.rsplit('.', 1)[-1] in short


def _bindings(pattern: str, expr: Expression) -> dict[int, Expression] | None:
    """Return the wildcard bindings of the first sub-expression of `expr` that matches the pattern."""
    wilds = {f'w{i}': SR.wild(i) for i in range(WILDCARDS)}
    compiled = parse_symbolic(pattern, wilds)
    if compiled is None:
        message = f'rewrite pattern {pattern!r} does not parse'
        raise CertificateError(message)
    for sub in expr.find(compiled):
        match = sub.match(compiled)
        if match:
            return {i: match[SR.wild(i)] for i in range(WILDCARDS) if SR.wild(i) in match}
    return None


def _fill(template: str, bindings: Mapping[int, Expression], problem: Problem) -> str:
    """Replace each `#i` in a side-condition template by the Lean text of the argument bound to `wi`."""
    return re.sub(r'#(\d+)', lambda m: str(symbolic(bindings[int(m.group(1))], problem, lean_type='')), template)


def rewrite_candidates(problem: Problem) -> list[RewriteCandidate]:
    """Return the rewrites the problem's tables (core, packs, project) offer for its goal, in table order.

    An entry applies when the goal mentions every function it names, and, when it has a pattern, when the pattern
    matches the goal's symbolic form; the pattern's bindings then fill the side conditions.

    Args:
        problem: The problem.

    Returns:
        The applicable rewrites.

    Examples:
        >>> from veriphy.toolkit import read_problem
        >>> prob = read_problem({'vars': ['x0', 'x1'], 'atoms': ['x', 'y'], 'carrier': 'ℝ',
        ...     'hyps': [{'name': 'hx', 'poly': 'x0', 'rel': 'ne', 'text': 'x ≠ 0'},
        ...              {'name': 'hy', 'poly': 'x1', 'rel': 'ne', 'text': 'y ≠ 0'}],
        ...     'goal': {'kind': 'other', 'rel': 'eq', 'expr': '(log((x0 * x1))) - ((log(x0) + log(x1)))',
        ...              'text': 'Real.log (x * y) = Real.log x + Real.log y'}})
        >>> [str(c.emit(prob)) for c in rewrite_candidates(prob)]
        ['rw [Real.log_mul (by assumption) (by assumption)]']
    """
    goal = problem.goal
    text = goal.text if goal is not None else ''
    expr = goal.expr if goal is not None and isinstance(goal.expr, Expression) else None
    found = []
    for table in problem.tables:
        for entry in table.rewrites:
            if not all(_mentions(f, text) for f in entry.functions):
                continue
            side = entry.side
            if entry.pattern is not None:
                bindings = _bindings(entry.pattern, expr) if expr is not None else None
                if bindings is None:
                    continue
                side = tuple(_fill(t, bindings, problem) for t in side)
            found.append(RewriteCandidate(entry.lemma, entry.reverse, side, table.namespace))
    return found
