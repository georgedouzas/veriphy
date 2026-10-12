"""Bind a serialized Lean problem to Sage objects."""

import re
from dataclasses import dataclass, field

from sage.all import (
    QQ,
    SR,
    I,
    PolynomialRing,
    abs_symbolic,
    cos,
    exp,
    function,
    log,
    matrix,
    pi,
    product,
    sage_eval,
    sin,
    sqrt,
    tan,
)
from sage.all import sum as symbolic_sum
from sage.matrix.matrix0 import Matrix
from sage.rings.polynomial.multi_polynomial import MPolynomial
from sage.rings.polynomial.multi_polynomial_ring_base import MPolynomialRing_base
from sage.symbolic.expression import Expression

from veriphy.core import RELATIONS, CertificateError, ParamError
from veriphy.toolkit._table import Table, load_core_table

GOAL_KINDS = ('rel', 'false', 'exists', 'other')
DOMAIN_KINDS = ('ne', 'nonneg', 'pos', 'le')
BOUND = re.compile(r'\b[^\W\d]\w*_\b')
mod = function('mod', nargs=2)


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


def parse_symbolic(text: object, symbols: dict[str, Expression]) -> Expression | Matrix | None:
    """Parse a symbolic expression serialized by Lean's symbolic translation, or return `None` when it does not parse.

    Args:
        text: The expression in Sage syntax, over the variables in `symbols`.
        symbols: The symbolic variables by name.

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
        'typed': lambda e, _ty: e,
        'matrix': matrix,
    }
    names.update({k: SR.var(k) for k in BOUND.findall(text)})
    names.update(symbols)
    try:
        value = sage_eval(text, locals=names)
    except (TypeError, ValueError, SyntaxError, NameError, ArithmeticError, AttributeError):
        return None
    return value if isinstance(value, Expression | Matrix) else SR(value)


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


def _read_constraint(item: object, where: str, ring: MPolynomialRing_base, symbols: dict[str, Expression]) -> Hyp:
    """Return one serialized hypothesis or goal as a `Hyp`, with or without polynomial and symbolic forms."""
    if not isinstance(item, dict):
        raise ParamError(param='problem', reason=f'{where}: must be an object')
    text = str(item.get('text', ''))
    expr = parse_symbolic(item.get('expr'), symbols)
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
) -> list[Hyp]:
    """Return a serialized list of constraints as `Hyp`s, empty for anything that is not a list."""
    items = items if isinstance(items, list) else []
    return [_read_constraint(h, f'{where} {i}', ring, symbols) for i, h in enumerate(items)]


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
    symbols = {n: SR.var(n) for n in names}
    bound = Problem(
        ring=ring,
        hyps=_read_constraints(problem.get('hyps', []), 'constraint', ring, symbols),
        goal_kind=kind,
        atoms={n: str(a) for n, a in zip(names, atoms if isinstance(atoms, list) else [], strict=False)},
        carrier=str(problem.get('carrier', '')),
        atom_types={n: str(t) for n, t in zip(names, types if isinstance(types, list) else [], strict=False)},
        domain=_read_domain(problem.get('domain', []), symbols),
        symbols=symbols,
    )
    if kind in ('rel', 'other'):
        bound.goal = _read_constraint({**goal, 'name': None}, 'goal', ring, symbols)
    if kind == 'rel' and 'lhs_poly' in goal:
        bound.lhs = Side(parse_polynomial(ring, goal.get('lhs_poly'), param='problem'), str(goal.get('lhs', '')))
        bound.rhs = Side(parse_polynomial(ring, goal.get('rhs_poly'), param='problem'), str(goal.get('rhs', '')))
    elif kind == 'exists':
        bound.binders = list(ring.gens()[: int(str(goal.get('binders', 0)))])
        bound.body = _read_constraints(goal.get('body', []), 'body', ring, symbols)
    return bound
