"""Bind a serialized Lean problem to Sage objects."""

import re
from dataclasses import dataclass, field

from sage.all import (
    QQ,
    SR,
    I,
    Integer,
    PolynomialRing,
    abs_symbolic,
    arccos,
    arcsin,
    arctan,
    binomial,
    block_matrix,
    ceil,
    cos,
    cosh,
    exp,
    factorial,
    floor,
    function,
    log,
    matrix,
    max_symbolic,
    min_symbolic,
    pi,
    product,
    sage_eval,
    sin,
    sinh,
    sqrt,
    tan,
    tanh,
)
from sage.all import sum as symbolic_sum
from sage.matrix.matrix0 import Matrix
from sage.rings.polynomial.multi_polynomial import MPolynomial
from sage.rings.polynomial.multi_polynomial_ring_base import MPolynomialRing_base
from sage.symbolic.expression import Expression

from veriphy.core import RELATIONS, CertificateError, ParamError
from veriphy.toolkit._table import Table, load_core_table, load_pack, parse_table

GOAL_KINDS = ('rel', 'false', 'exists', 'other')
DOMAIN_KINDS = ('ne', 'nonneg', 'pos', 'le')
BOUND = re.compile(r'\b[^\W\d]\w*_\b')
mod = function('mod', nargs=2)
CORE_NAMESPACE = 'mathlib'
PROJECT_NAMESPACE = 'project'


def _integer_gcd(_self: object, a: Expression, b: Expression) -> Expression | None:
    """Evaluate `gcd` on integer numerals only; Sage's own `gcd` treats a symbol as a polynomial and returns 1."""
    if SR(a).is_integer() and SR(b).is_integer():
        return SR(Integer(a).gcd(Integer(b)))
    return None


integer_gcd = function('gcd', nargs=2, eval_func=_integer_gcd)


def create_ring(names: list[str]) -> MPolynomialRing_base:
    """Create the multivariate polynomial ring QQ[names], multivariate even for one name.

    Args:
        names: The variable names, valid identifiers.

    Returns:
        The polynomial ring.

    Examples:
        >>> create_ring(['x0', 'x1']).gens()
        (x0, x1)
    """
    return PolynomialRing(QQ, len(names), names)


def parse_polynomial(ring: MPolynomialRing_base, s: object, *, param: str) -> MPolynomial:
    """Parse a polynomial string in `ring`.

    Args:
        ring: The polynomial ring.
        s: The polynomial, written in Sage syntax.
        param: The request parameter the string came from, named in errors.

    Returns:
        The polynomial.

    Raises:
        ParamError: If `s` is not a string or not a polynomial in `ring`.

    Examples:
        >>> parse_polynomial(create_ring(['x0']), 'x0^2 - 1/2', param='poly')
        x0^2 - 1/2
    """
    if not isinstance(s, str):
        raise ParamError(param=param, reason='must be a polynomial string')
    try:
        return ring(s)
    except (TypeError, ValueError, SyntaxError, NameError) as exc:
        gens = ', '.join(map(str, ring.gens()))
        raise ParamError(param=param, reason=f'not a polynomial in QQ[{gens}]: {s!r} ({exc})') from exc


@dataclass(frozen=True)
class Side:
    """Hold one side of a relation goal, as scripts see it.

    Args:
        poly: The side as a polynomial of the problem's ring.
        text: The side's Lean text, exactly as the goal writes it.
    """

    poly: MPolynomial
    text: str


def parse_symbolic(
    text: object,
    symbols: dict[str, Expression],
    typed: list[tuple[Expression, str]] | None = None,
) -> Expression | Matrix | None:
    """Parse a symbolic expression serialized by Lean's symbolic translation, or return `None` when it does not parse.

    `typed(e, 'ℕ')` markers (a sub-expression computed at another Lean type) evaluate to `e`, and are recorded in
    `typed` when a list is given.

    Args:
        text: The expression in Sage syntax, over the variables in `symbols`.
        symbols: The symbolic variables by name.
        typed: Where to record the marked sub-expressions with their Lean type.

    Returns:
        The expression in Sage's symbolic ring (a matrix over it for a matrix-valued expression), or `None`.

    Examples:
        >>> x0 = SR.var('x0')
        >>> parse_symbolic('(sqrt(x0) + log(x0))', {'x0': x0})
        sqrt(x0) + log(x0)
        >>> parse_symbolic('sum((k_)^(2), k_, 0, x0 - 1)', {'x0': x0})
        1/3*x0^3 - 1/2*x0^2 + 1/6*x0
        >>> parse_symbolic('mod(x0, 3)', {'x0': x0})
        mod(x0, 3)
        >>> parse_symbolic('(matrix(SR, [[1, x0]])) - (matrix(SR, [[1, 0]]))', {'x0': x0})
        [ 0 x0]
        >>> marked = []
        >>> parse_symbolic("typed(mod(x0, 7), 'ℕ') + gcd(x0, 6) + gcd(4, 6)", {'x0': x0}, marked)
        gcd(x0, 6) + mod(x0, 7) + 2
        >>> marked
        [(mod(x0, 7), 'ℕ')]
    """
    if not isinstance(text, str):
        return None
    names: dict[str, object] = {
        'SR': SR,
        'pi': pi,
        'I': I,
        'X': SR.var('X'),
        'sqrt': sqrt,
        'exp': exp,
        'log': log,
        'sin': sin,
        'cos': cos,
        'tan': tan,
        'abs': abs_symbolic,
        'mod': mod,
        'sum': symbolic_sum,
        'product': product,
        'typed': lambda e, ty: _record(typed, e, ty),
        'cosh': cosh,
        'sinh': sinh,
        'tanh': tanh,
        'arcsin': arcsin,
        'arccos': arccos,
        'arctan': arctan,
        'logb': lambda b, x: log(x) / log(b),
        'floor': floor,
        'ceil': ceil,
        'factorial': factorial,
        'binomial': binomial,
        'gcd': integer_gcd,
        'matrix': matrix,
        'block_matrix': block_matrix,
        'max': max_symbolic,
        'min': min_symbolic,
    }
    names.update({k: SR.var(k) for k in BOUND.findall(text)})
    names.update(symbols)
    try:
        value = sage_eval(text, locals=names)
    except (TypeError, ValueError, SyntaxError, NameError, ArithmeticError, AttributeError):
        return None
    return value if isinstance(value, Expression | Matrix) else SR(value)


def _record(typed: list[tuple[Expression, str]] | None, e: Expression, ty: str) -> Expression:
    """Record a `typed` marker's sub-expression and type, and return the sub-expression."""
    if typed is not None:
        typed.append((SR(e), str(ty)))
    return e


@dataclass(frozen=True)
class Definition:
    """Hold an explicit definition of an unknown function, from a hypothesis `x = fun s => body`.

    Args:
        function: The function's Sage name.
        var: The variable of the body, a Sage symbol.
        body: The body, in `var` and the problem's variables.
        hyp: The hypothesis stating the definition.
        text: The Lean text of the function (the lambda).
    """

    function: str
    var: Expression
    body: Expression | None
    hyp: str
    text: str


@dataclass(frozen=True)
class ExistsFunction:
    """Hold a goal `∃ x, C₁ ∧ C₂ ∧ …` over an unknown function.

    Args:
        function: The function's Sage name.
        lean: The binder's Lean name.
        conjuncts: Each conjunct as its universally quantified variable (`None` when none) and its symbolic form
            `lhs - rhs`, in the function and the problem's variables.
    """

    function: str
    lean: str
    conjuncts: tuple[tuple[Expression | None, Expression | None], ...]


@dataclass(frozen=True)
class MatrixIndex:
    """Hold the index type of a matrix indexed by sums of `Fin` types, such as `Fin 1 ⊕ Fin 3`.

    Args:
        rows: The sizes of the row index's summands, in order.
        cols: The sizes of the column index's summands, in order.
        text: The matrix type's Lean text.
    """

    rows: tuple[int, ...]
    cols: tuple[int, ...]
    text: str


@dataclass(frozen=True)
class Derivative:
    """Hold a derivative the translation met, `deriv f point`.

    Args:
        var: The variable of differentiation, a Sage symbol.
        body: The function's body, in `var` and the problem's variables.
        point: The point, over the problem's variables.
        function: The Lean text of the function.
        at: The Lean text of the point.
    """

    var: Expression
    body: Expression | None
    point: Expression | None
    function: str
    at: str


@dataclass(frozen=True)
class Condition:
    """Hold a domain condition a symbolic expression of the problem needs.

    Args:
        text: The Lean text of the condition, such as `y ≠ 0`.
        expr: The constrained expression, in Sage's symbolic ring, or `None` when it does not parse.
        kind: `ne` (`e ≠ 0`), `nonneg` (`0 ≤ e`), `pos` (`0 < e`) or `le` (`e ≤ bound`).
        discharged_by: The hypothesis that states it, or `None`.
        bound: The upper bound of an `le` condition, in Sage's symbolic ring.
    """

    text: str
    expr: Expression | Matrix | None
    kind: str
    discharged_by: str | None = None
    bound: Expression | Matrix | None = None


@dataclass(frozen=True)
class Hyp:
    """Hold one hypothesis or goal of a problem, as scripts see it.

    Args:
        name: The Lean hypothesis name, or `None` for the goal and existential body.
        poly: The polynomial `p` of the constraint `p rel 0`, or `None` when it has no polynomial form.
        rel: The relation tag, one of `eq`, `le`, `lt`, `ne`, or `None` without a polynomial form.
        text: The Lean text of the proposition.
        expr: The symbolic form `e` of `e rel 0` (or of the proposition's sides' difference), or `None`.
    """

    name: str | None
    poly: MPolynomial | None
    rel: str | None
    text: str = ''
    expr: Expression | Matrix | None = None


@dataclass
class Problem:
    """Hold a serialized Lean problem bound to Sage objects.

    Args:
        ring: The polynomial ring over the problem's atoms.
        hyps: The hypotheses.
        goal_kind: One of `rel`, `false`, `exists` and `other`.
        goal: The goal of a `rel` or `other` goal, with its Lean text.
        binders: The generators bound by an `exists` goal.
        body: The constraints of an `exists` goal.
        atoms: The Lean text of each variable, by variable name.
        carrier: The Lean text of the type the problem's polynomials live in (such as `ℚ`), empty when unknown.
        lhs: The left side of a relation goal, when the goal has a polynomial form.
        rhs: The right side of a relation goal, when the goal has a polynomial form.
        atom_types: The Lean type of each variable (`ℕ`, `ℤ`, `ℚ`, `ℝ`, `ℂ`, `matrix` or `other`), by name.
        domain: The domain conditions the problem's symbolic expressions need.
        symbols: The variables as symbolic-ring variables, by name, for symbolic work.
        tables: The translation tables in force, core first.
        typed: The sub-expressions Lean computes at another type (`ℕ`, `ℤ`) than their context, with that type.
        derivatives: The derivatives the translation met, in the order it met them.
        functions: The unknown functions, by Sage name: their Lean name and arity.
        definitions: Explicit definitions of unknown functions from the hypotheses.
        exists_function: The goal's existential over an unknown function, when it is one.
        matrix_indices: The index types of the matrices indexed by sums of `Fin` types, for rendering them back.
    """

    ring: MPolynomialRing_base
    hyps: list[Hyp]
    goal_kind: str
    goal: Hyp | None = None
    binders: list[MPolynomial] = field(default_factory=list)
    body: list[Hyp] = field(default_factory=list)
    atoms: dict[str, str] = field(default_factory=dict)
    carrier: str = ''
    lhs: Side | None = None
    rhs: Side | None = None
    atom_types: dict[str, str] = field(default_factory=dict)
    domain: list[Condition] = field(default_factory=list)
    symbols: dict[str, Expression] = field(default_factory=dict)
    tables: tuple[Table, ...] = field(default_factory=lambda: (load_core_table(),))
    typed: list[tuple[Expression, str]] = field(default_factory=list)
    derivatives: list[Derivative] = field(default_factory=list)
    functions: dict[str, tuple[str, int]] = field(default_factory=dict)
    definitions: list[Definition] = field(default_factory=list)
    exists_function: ExistsFunction | None = None
    matrix_indices: list[MatrixIndex] = field(default_factory=list)

    def find_hyp(self, name: str, allowed: tuple[str, ...], family: str) -> Hyp:
        """Find the hypothesis named `name`, checking its relation is usable by `family`.

        Args:
            name: The hypothesis name.
            allowed: The relation tags `family` accepts.
            family: The proof shape asking, named in errors.

        Returns:
            The hypothesis.

        Raises:
            CertificateError: If no hypothesis has that name, or its relation is not in `allowed`.
        """
        by_name = {h.name: h for h in self.hyps}
        if name not in by_name:
            message = f"certificate names unknown hypothesis '{name}' (known: {sorted(map(str, by_name))})"
            raise CertificateError(message)
        hyp = by_name[name]
        if hyp.rel not in allowed:
            message = f"hypothesis '{name}' has relation '{hyp.rel}', not usable by {family}"
            raise CertificateError(message)
        return hyp

    def to_namespace(self) -> dict[str, object]:
        """Return the names a script sees.

        Returns:
            `problem`, `R`, the generators by name, `hyps`, `goal`, `goal_kind`, `binders`, `body`, `atoms`, `lhs`,
            `rhs`, `domain`, `symbols` and `Hyp`.
        """
        names: dict[str, object] = {
            'problem': self,
            'R': self.ring,
            'Hyp': Hyp,
            'hyps': self.hyps,
            'goal': self.goal,
            'goal_kind': self.goal_kind,
            'binders': self.binders,
            'body': self.body,
            'atoms': self.atoms,
            'lhs': self.lhs,
            'rhs': self.rhs,
            'domain': self.domain,
            'symbols': self.symbols,
        }
        names.update({str(g): g for g in self.ring.gens()})
        return names


def _read_constraint(
    item: object,
    where: str,
    ring: MPolynomialRing_base,
    symbols: dict[str, Expression],
    typed: list[tuple[Expression, str]],
) -> Hyp:
    """Return one serialized hypothesis or goal as a `Hyp`, with or without polynomial and symbolic forms."""
    if not isinstance(item, dict):
        raise ParamError(param='problem', reason=f'{where}: must be an object')
    text = str(item.get('text', ''))
    expr = parse_symbolic(item.get('expr'), symbols, typed)
    rel = item.get('rel')
    if rel is not None and rel not in RELATIONS:
        raise ParamError(param='problem', reason=f'{where}: bad relation {rel!r}')
    if item.get('poly') is None:
        return Hyp(item.get('name'), None, str(rel) if rel and expr is not None else None, text, expr)
    if rel is None:
        raise ParamError(param='problem', reason=f'{where}: bad relation {rel!r}')
    return Hyp(item.get('name'), parse_polynomial(ring, item.get('poly'), param='problem'), str(rel), text, expr)


def _read_constraints(
    items: object,
    where: str,
    ring: MPolynomialRing_base,
    symbols: dict[str, Expression],
    typed: list[tuple[Expression, str]],
) -> list[Hyp]:
    """Return a serialized list of constraints as `Hyp`s, empty for anything that is not a list."""
    items = items if isinstance(items, list) else []
    return [_read_constraint(h, f'{where} {i}', ring, symbols, typed) for i, h in enumerate(items)]


def _read_domain(items: object, symbols: dict[str, Expression]) -> list[Condition]:
    """Return the serialized domain conditions, skipping malformed entries."""
    conditions = []
    for item in items if isinstance(items, list) else []:
        if not isinstance(item, dict) or item.get('kind') not in DOMAIN_KINDS:
            raise ParamError(param='problem', reason=f'bad domain condition {item!r}')
        by = item.get('discharged_by')
        expr = parse_symbolic(item.get('expr'), symbols)
        bound = parse_symbolic(item.get('bound'), symbols)
        text = str(item.get('text', ''))
        conditions.append(Condition(text, expr, str(item['kind']), str(by) if by else None, bound))
    return conditions


def _read_tables(problem: dict[str, object]) -> tuple[Table, ...]:
    """Return the translation tables the problem was extracted with: the core, its active packs, its project entries."""
    names = problem.get('namespaces') or [CORE_NAMESPACE]
    if not isinstance(names, list):
        raise ParamError(param='problem', reason="'namespaces' must be a list")
    packs = [load_pack(str(n)) for n in names if n not in (CORE_NAMESPACE, PROJECT_NAMESPACE)]
    extensions = problem.get('extensions') or []
    if not isinstance(extensions, list):
        raise ParamError(param='problem', reason="'extensions' must be a list")
    project = [parse_table(t, f'problem extension {i}') for i, t in enumerate(extensions)]
    return (load_core_table(), *packs, *project)


def _read_derivatives(items: object, symbols: dict[str, Expression]) -> list[Derivative]:
    """Return the serialized derivatives, each body parsed with its own variable."""
    derivatives = []
    for item in items if isinstance(items, list) else []:
        if not isinstance(item, dict) or not isinstance(item.get('var'), str):
            raise ParamError(param='problem', reason=f'bad derivative {item!r}')
        var = SR.var(str(item['var']))
        body = parse_symbolic(item.get('body'), {**symbols, str(var): var})
        point = parse_symbolic(item.get('point'), symbols)
        derivatives.append(Derivative(var, body, point, str(item.get('function', '')), str(item.get('at', ''))))
    return derivatives


def _read_functions(items: object) -> dict[str, tuple[str, int]]:
    """Return the unknown functions by Sage name: Lean name and arity."""
    functions = {}
    for item in items if isinstance(items, list) else []:
        if not isinstance(item, dict) or not str(item.get('sage', '')).isidentifier():
            raise ParamError(param='problem', reason=f'bad function {item!r}')
        functions[str(item['sage'])] = (str(item.get('lean', '')), int(str(item.get('arity', 1))))
    return functions


def _read_definitions(items: object, symbols: dict[str, Expression]) -> list[Definition]:
    """Return the explicit definitions of unknown functions."""
    definitions = []
    for item in items if isinstance(items, list) else []:
        if not isinstance(item, dict):
            raise ParamError(param='problem', reason=f'bad definition {item!r}')
        var = SR.var(str(item.get('var', 's_')))
        body = parse_symbolic(item.get('body'), {**symbols, str(var): var})
        definitions.append(
            Definition(str(item.get('function')), var, body, str(item.get('hyp')), str(item.get('text'))),
        )
    return definitions


def _read_exists_function(item: object, symbols: dict[str, Expression]) -> ExistsFunction | None:
    """Return the goal's existential over an unknown function, or `None`."""
    if not isinstance(item, dict):
        return None
    conjuncts = []
    for c in item.get('conjuncts', []) if isinstance(item.get('conjuncts'), list) else []:
        var = SR.var(str(c['var'])) if c.get('var') else None
        scope = {**symbols, str(var): var} if var is not None else symbols
        conjuncts.append((var, parse_symbolic(c.get('expr'), scope)))
    return ExistsFunction(str(item.get('function')), str(item.get('lean')), tuple(conjuncts))


def _read_matrix_indices(items: object) -> list[MatrixIndex]:
    """Return the index types of the problem's sum-indexed matrices."""
    if not isinstance(items, list):
        return []
    return [
        MatrixIndex(tuple(int(n) for n in i.get('rows', [])), tuple(int(n) for n in i.get('cols', [])), str(i['text']))
        for i in items
        if isinstance(i, dict) and 'text' in i
    ]


def _read_names(problem: dict[str, object]) -> list[str]:
    """Return the problem's variable names, or a single placeholder name for a problem without atoms."""
    names = problem.get('vars') or []
    if not isinstance(names, list) or not all(isinstance(n, str) and n.isidentifier() for n in names):
        raise ParamError(param='problem', reason="'vars' must be a list of identifiers")
    return names or ['x0']


def read_problem(problem: object) -> Problem:
    """Bind a serialized Lean problem to Sage objects.

    Args:
        problem: The problem as `Veriphy.Problem.toJson` serializes it.

    Returns:
        The bound problem.

    Raises:
        ParamError: If the serialization is malformed.

    Examples:
        >>> bound = read_problem({'vars': ['x0'], 'atoms': ['x'],
        ...     'hyps': [{'name': 'h', 'poly': 'x0 - 1', 'rel': 'le', 'text': 'x ≤ 1'},
        ...              {'name': 'hs', 'text': 'Real.sin x ≤ 1'}],
        ...     'goal': {'kind': 'other', 'text': 'Real.cos x ≤ 1'}})
        >>> [(h.name, h.poly, h.rel) for h in bound.hyps]
        [('h', x0 - 1, 'le'), ('hs', None, None)]
        >>> bound.goal.text
        'Real.cos x ≤ 1'
    """
    if not isinstance(problem, dict):
        raise ParamError(param='problem', reason='must be an object')
    names = _read_names(problem)
    ring = create_ring(names)
    goal = problem.get('goal') or {'kind': 'false'}
    goal = goal if isinstance(goal, dict) else {}
    kind = str(goal.get('kind'))
    if kind not in GOAL_KINDS:
        raise ParamError(param='problem', reason=f'unknown goal kind {kind!r}')
    atoms = problem.get('atoms', [])
    types = problem.get('atom_types', [])
    functions = _read_functions(problem.get('functions', []))
    symbols = {n: SR.var(n) for n in names}
    symbols.update({name: function(name) for name in functions})
    typed: list[tuple[Expression, str]] = []
    bound = Problem(
        ring=ring,
        hyps=_read_constraints(problem.get('hyps', []), 'constraint', ring, symbols, typed),
        goal_kind=kind,
        atoms={n: str(a) for n, a in zip(names, atoms if isinstance(atoms, list) else [], strict=False)},
        carrier=str(problem.get('carrier', '')),
        atom_types={n: str(t) for n, t in zip(names, types if isinstance(types, list) else [], strict=False)},
        domain=_read_domain(problem.get('domain', []), symbols),
        symbols=symbols,
        tables=_read_tables(problem),
        typed=typed,
        derivatives=_read_derivatives(problem.get('derivatives', []), symbols),
        functions=functions,
        definitions=_read_definitions(problem.get('definitions', []), symbols),
        exists_function=_read_exists_function(problem.get('exists_function'), symbols),
        matrix_indices=_read_matrix_indices(problem.get('matrix_indices')),
    )
    if kind in ('rel', 'other'):
        bound.goal = _read_constraint({**goal, 'name': None}, 'goal', ring, symbols, typed)
    if kind == 'rel' and 'lhs_poly' in goal:
        bound.lhs = Side(parse_polynomial(ring, goal.get('lhs_poly'), param='problem'), str(goal.get('lhs', '')))
        bound.rhs = Side(parse_polynomial(ring, goal.get('rhs_poly'), param='problem'), str(goal.get('rhs', '')))
    elif kind == 'exists':
        bound.binders = list(ring.gens()[: int(str(goal.get('binders', 0)))])
        bound.body = _read_constraints(goal.get('body', []), 'body', ring, symbols, typed)
    return bound
