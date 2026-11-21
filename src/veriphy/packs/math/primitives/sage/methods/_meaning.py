"""Test whether a claim's statement means what it was meant to: evaluate it at seeded values satisfying its hypotheses.

The Sage session's `meaning` method draws values for the claim's universal binders with the toolkit's seeded `Sampler`,
keeps those at which every hypothesis and every domain condition holds, and decides the conclusion at each exactly,
or in interval arithmetic of `PRECISION` bits when Sage cannot. A value at which an interval cannot decide counts as
undecided, never as agreement. An equation is first tried symbolically, under the hypotheses, and only when every
domain condition follows from a hypothesis, since Sage's algebra knows nothing of Lean's junk values (`x / 0 = 0`).
"""

from collections import Counter
from collections.abc import Iterator, Mapping
from dataclasses import dataclass, field

from sage.all import QQ, SR, RealIntervalField, assume, forget, version
from sage.matrix.matrix0 import Matrix
from sage.symbolic.expression import Expression

from veriphy.core import JsonObject, JsonValue, Method, ParamError
from veriphy.packs.math.primitives.sage.methods._registry import _coerce_int, _coerce_json, _register_method
from veriphy.packs.math.script import Condition, Hyp, Problem, Sampler, parse_symbolic, read_problem

MEANING_METHODS: dict[str, Method] = {}
PRECISION = 128
DRAWS = 200
# the bound on a drawn rational's numerator and denominator
HEIGHT = 20
DEFAULT_VALUES = 10
SCALARS = {'ℕ': 'integer', 'ℤ': 'integer', 'ℚ': 'real', 'ℝ': 'real'}
EDGES = {'ℕ': (0, 1), 'ℤ': (0, 1, -1), 'ℚ': (0, 1, -1), 'ℝ': (0, 1, -1)}
FIELD = RealIntervalField(PRECISION)


class UndecidedError(Exception):
    """The statement cannot be tested, for the reason given."""


@dataclass
class Tally:
    """What happened to the values drawn: kept, agreeing, and why the others were set aside."""

    draws: int = 0
    distinct: int = 0
    kept: list[dict[str, str]] = field(default_factory=list)
    agreed: int = 0
    undecided: int = 0
    rejected: Counter[str] = field(default_factory=Counter)


def _decide(e: object, rel: str) -> bool | None:
    """Return whether `e rel 0` holds for a constant `e`: exactly when Sage can, else by an interval, else `None`.

    Args:
        e: The constant, an expression with no variables left.
        rel: `eq`, `ne`, `le` or `lt`.

    Returns:
        Whether the relation holds, or `None` when an interval of `PRECISION` bits cannot tell.

    Examples:
        >>> from sage.all import sqrt, pi
        >>> _decide(SR(1) / 2, 'le'), _decide(sqrt(2) - 1, 'lt'), _decide(pi - 3, 'eq')
        (False, False, False)
        >>> _decide(sqrt(SR(1) / 4) - SR(1) / 2, 'eq')
        True
    """
    value = SR(e)
    try:
        q = QQ(value)
    except (TypeError, ValueError, ArithmeticError):
        q = None
    if q is None:
        try:
            simplified = value.simplify_full()
        except (TypeError, ValueError, ArithmeticError, RuntimeError):
            simplified = value
        if simplified.is_trivial_zero():
            q = QQ(0)
    if q is not None:
        return {'eq': q == 0, 'ne': q != 0, 'le': q <= 0, 'lt': q < 0}[rel]
    try:
        x = FIELD(value)
    except (TypeError, ValueError, ArithmeticError, RuntimeError):
        return None
    zero = x.contains_zero()
    if rel == 'eq':
        return False if not zero else None
    if rel == 'ne':
        return True if not zero else None
    if rel == 'le':
        return True if x.upper() <= 0 else False if x.lower() > 0 else None
    return True if x.upper() < 0 else False if x.lower() >= 0 else None


def _show(e: object) -> str:
    """Return a constant as text: exact when it is rational or Sage prints it closed, with its interval besides."""
    value = SR(e)
    try:
        return str(QQ(value))
    except (TypeError, ValueError, ArithmeticError):
        pass
    try:
        return f'{value} ≈ {FIELD(value).str(style="brackets")}'
    except (TypeError, ValueError, ArithmeticError, RuntimeError):
        return str(value)


def _sides(source: str | None) -> tuple[str, str] | None:
    """Split a serialized relation `(a) - (b)` into its two sides.

    Args:
        source: The relation as Lean's symbolic translation serialized it.

    Returns:
        The two sides' Sage texts, or `None` when the text has another shape.

    Examples:
        >>> _sides('(sqrt((x1)^(2))) - ((-x1))')
        ('sqrt((x1)^(2))', '(-x1)')
    """
    if not source or not source.startswith('('):
        return None
    depth = 0
    for i, ch in enumerate(source):
        depth += {'(': 1, ')': -1}.get(ch, 0)
        if depth == 0:
            rest = source[i + 1 :]
            if rest.startswith(' - (') and rest.endswith(')'):
                return source[1:i], rest[4:-1]
            return None
    return None


@dataclass(frozen=True)
class Statement:
    """A claim's statement, bound for evaluation: its binders, hypotheses, conditions and conclusion."""

    problem: Problem
    binders: dict[str, tuple[Expression, str]]
    hyps: list[Hyp]
    goal: Hyp


def _binders(problem: Problem) -> dict[str, tuple[Expression, str]]:
    """Return each universal binder's variable and type, or raise `UndecidedError` for a binder that is no scalar."""
    by_text = {text: name for name, text in problem.atoms.items()}
    binders: dict[str, tuple[Expression, str]] = {}
    for name, kind in problem.universal:
        if kind not in SCALARS:
            message = f'the binder {name} : {kind} is not a scalar; give the values with points'
            raise UndecidedError(message)
        var = by_text.get(name)
        binders[name] = (problem.symbols[var] if var else SR.var(f'unused_{name}'), kind)
    return binders


def _conclusion(problem: Problem) -> Hyp:
    """Return the conclusion to evaluate, `False` as `0 ≠ 0`, or raise `UndecidedError` when it has no usable form."""
    if problem.goal_kind == 'exists':
        message = 'the statement is existential; the meaning check evaluates universal statements'
        raise UndecidedError(message)
    goal = Hyp(None, None, 'ne', 'False', SR(0), '(0) - (0)') if problem.goal_kind == 'false' else problem.goal
    if goal is None or goal.expr is None or goal.rel is None or isinstance(goal.expr, Matrix):
        message = 'the conclusion has no symbolic form Sage can evaluate'
        raise UndecidedError(message)
    return goal


def _bind(problem: Problem) -> Statement:
    """Return the statement to evaluate, or raise `UndecidedError` when part of it has no form Sage can evaluate."""
    binders = _binders(problem)
    goal = _conclusion(problem)
    for h in problem.hyps:
        if h.expr is None or h.rel is None or isinstance(h.expr, Matrix):
            message = f'the hypothesis {h.name} ({h.text}) has no symbolic form Sage can evaluate'
            raise UndecidedError(message)
    known = {v for v, _ in binders.values()}
    for e in [goal.expr, *(h.expr for h in problem.hyps), *(c.expr for c in problem.domain)]:
        for v in SR(e).variables() if isinstance(e, Expression) else ():
            if v not in known and not str(v).endswith('_'):
                text = problem.atoms.get(str(v), str(v))
                message = f'the statement depends on {text}, which is not one of its binders'
                raise UndecidedError(message)
    return Statement(problem, binders, problem.hyps, goal)


def _symbolic(statement: Statement) -> bool:
    """Return whether the conclusion, an equation, simplifies to an identity under the hypotheses."""
    if statement.goal.rel != 'eq' or any(c.discharged_by is None for c in statement.problem.domain):
        return False
    relations = {'eq': lambda e: e == 0, 'le': lambda e: e <= 0, 'lt': lambda e: e < 0}
    try:
        for var, kind in statement.binders.values():
            assume(var, SCALARS[kind])
        for h in statement.hyps:
            if h.rel in relations:
                assume(relations[h.rel](SR(h.expr)))
        return bool(SR(statement.goal.expr).simplify_full().is_trivial_zero())
    except (TypeError, ValueError, ArithmeticError, RuntimeError):
        return False
    finally:
        forget()


def _draws(statement: Statement, seed: int) -> Iterator[dict[str, object]]:
    """Yield `DRAWS` seeded values for the binders: the edge cases first (zero, one, minus one), then samples."""
    sampler = Sampler(seed)
    kinds = {name: kind for name, (_, kind) in statement.binders.items()}
    for k in range(max(len(e) for e in EDGES.values())):
        yield {name: QQ(EDGES[kind][min(k, len(EDGES[kind]) - 1)]) for name, kind in kinds.items()}
    for _ in range(DRAWS - len(EDGES['ℝ'])):
        point: dict[str, object] = {}
        for name, kind in kinds.items():
            if kind == 'ℕ':
                point[name] = sampler.integer(0, 9)
            elif kind == 'ℤ':
                point[name] = sampler.integer(-9, 9)
            else:
                point[name] = sampler.rational(HEIGHT)
        yield point


def _given(points: JsonValue, statement: Statement) -> list[dict[str, object]]:
    """Return the points the caller gave, each value parsed by Sage (so `pi` and `sqrt(2)` are exact)."""
    if not isinstance(points, list) or not points:
        raise ParamError(param='points', reason='must be a non-empty list of objects from binder name to value')
    parsed = []
    for point in points:
        if not isinstance(point, dict) or set(point) != set(statement.binders):
            raise ParamError(param='points', reason=f'each point names every binder: {sorted(statement.binders)}')
        values = {name: parse_symbolic(str(text), {}) for name, text in point.items()}
        missing = [name for name, v in values.items() if v is None]
        if missing:
            raise ParamError(param='points', reason=f'Sage cannot read the value of {missing[0]}')
        parsed.append(values)
    return parsed


def _substitution(statement: Statement, point: Mapping[str, object]) -> dict[Expression, object]:
    """Return the substitution of a point's values for the binders' variables."""
    return {var: point[name] for name, (var, _) in statement.binders.items()}


def _holds(condition: Condition, subs: dict[Expression, object]) -> bool | None:
    """Return whether a domain condition holds at a point, `None` when it cannot be decided."""
    e = SR(condition.expr).subs(subs)
    if condition.kind == 'ne':
        return _decide(e, 'ne')
    if condition.kind == 'nonneg':
        return _decide(-e, 'le')
    if condition.kind == 'pos':
        return _decide(-e, 'lt')
    return _decide(e - SR(condition.bound), 'le') if condition.bound is not None else None


def _rejection(statement: Statement, subs: dict[Expression, object]) -> str | None:
    """Return why a point cannot test the statement (a hypothesis or condition fails or is undecided), or `None`."""
    for h in statement.hyps:
        if _decide(SR(h.expr).subs(subs), str(h.rel)) is not True:
            return f'{h.name}: {h.text}'
    for c in statement.problem.domain:
        if not isinstance(c.expr, Expression):
            continue
        if _holds(c, subs) is not True:
            return f'domain: {c.text}'
    for e, kind in statement.problem.typed:
        value = SR(e).subs(subs)
        if value not in QQ or QQ(value).denominator() != 1 or (kind == 'ℕ' and QQ(value) < 0):
            return f'Lean computes {e} in {kind}'
    return None


def _counterexample(statement: Statement, subs: dict[Expression, object], values: dict[str, str]) -> JsonObject:
    """Return a counterexample: the values, both sides of the conclusion, and their difference."""
    goal = statement.goal
    sides = _sides(goal.source)
    lhs = rhs = '?'
    if sides is not None:
        parsed = [parse_symbolic(s, statement.problem.symbols) for s in sides]
        if all(isinstance(p, Expression) for p in parsed):
            lhs, rhs = (_show(SR(p).subs(subs)) for p in parsed)
    return {
        'values': dict(values),
        'statement': goal.text,
        'lhs': lhs,
        'rhs': rhs,
        'difference': _show(SR(goal.expr).subs(subs)),
    }


def _test(statement: Statement, points: Iterator[dict[str, object]] | list[dict[str, object]], target: int) -> tuple[
    Tally,
    JsonObject | None,
]:
    """Evaluate the statement at the points until `target` values agree, or one is a counterexample."""
    tally = Tally()
    seen: list[dict[str, str]] = []
    for point in points:
        tally.draws += 1
        values = {name: str(v) for name, v in point.items()}
        if values in seen:
            continue
        seen.append(values)
        tally.distinct += 1
        subs = _substitution(statement, point)
        reason = _rejection(statement, subs)
        if reason is not None:
            tally.rejected[reason] += 1
            continue
        tally.kept.append(values)
        verdict = _decide(SR(statement.goal.expr).subs(subs), str(statement.goal.rel))
        if verdict is False:
            return tally, _counterexample(statement, subs, values)
        if verdict is None:
            tally.undecided += 1
        else:
            tally.agreed += 1
        if tally.agreed >= target:
            break
    return tally, None


def _undecided_reason(tally: Tally, target: int) -> str:
    """Return why too few values agreed: the hypothesis or condition that rejected most, or undecided evaluations."""
    if tally.rejected and tally.rejected.most_common(1)[0][1] >= tally.undecided:
        culprit, count = tally.rejected.most_common(1)[0]
        return (
            f'{tally.agreed} of the {target} values needed agreed; {culprit} rejected {count} of the '
            f'{tally.distinct} distinct values drawn'
        )
    return f'{tally.agreed} of the {target} values needed agreed; {tally.undecided} evaluations were undecided'


def _coerce_optional(pname: str, req: JsonObject, _ctx: dict[str, object]) -> tuple[str, object]:
    """Return a parameter unchanged, `None` when it is absent."""
    return pname, req.get(pname)


def meaning(problem: object, seed: int, values: int, points: JsonValue = None) -> JsonObject:
    """Return the meaning check of a claim: `agrees`, `counterexample` or `undecided`, with what it evaluated.

    Args:
        problem: The claim's serialized problem, with its universal binders under `universal`.
        seed: The seed of the drawn values.
        values: How many drawn values must agree; when fewer do after `DRAWS` draws, the outcome is `undecided`.
        points: Values to evaluate at instead of drawn ones: a list of objects from binder name to Sage text.

    Returns:
        The outcome, the method (`symbolic`, `sampled` or `none`), the counts, the values kept, the counterexample
        and the reason of an undecided outcome.
    """
    read = read_problem(problem)
    result: JsonObject = {'seed': seed, 'target': values, 'sage_version': str(version())}
    try:
        statement = _bind(read)
    except UndecidedError as exc:
        return {**result, 'outcome': 'undecided', 'method': 'none', 'reason': str(exc)}
    if points is None and _symbolic(statement):
        return {**result, 'outcome': 'agrees', 'method': 'symbolic', 'agreed': 0, 'reason': None}
    given = None if points is None else _given(points, statement)
    target = values if given is None else len(given)
    tally, counterexample = _test(statement, given if given is not None else _draws(statement, seed), target)
    result.update(
        {
            'method': 'sampled',
            'given': given is not None,
            'target': target,
            'draws': tally.draws,
            'distinct': tally.distinct,
            'agreed': tally.agreed,
            'undecided': tally.undecided,
            'values': [dict(point) for point in tally.kept],
            'rejected': dict(tally.rejected),
        },
    )
    if counterexample is not None:
        return {**result, 'outcome': 'counterexample', 'counterexample': counterexample, 'reason': None}
    if tally.agreed < target:
        return {**result, 'outcome': 'undecided', 'reason': _undecided_reason(tally, target)}
    return {**result, 'outcome': 'agrees', 'reason': None, 'note': _skipped(tally)}


def _skipped(tally: Tally) -> str | None:
    """Return a note naming the domain conditions that set values aside, whose junk values in Lean went untested."""
    domain = {reason: n for reason, n in tally.rejected.items() if reason.startswith('domain: ')}
    if not domain:
        return None
    shown = ', '.join(f'{reason.removeprefix("domain: ")} ({n})' for reason, n in sorted(domain.items()))
    return f'untested where a domain condition fails, where Lean takes a junk value: {shown}'


_register_method(
    MEANING_METHODS,
    'meaning',
    problem=_coerce_json,
    seed=_coerce_int(0),
    values=_coerce_int(DEFAULT_VALUES),
    points=_coerce_optional,
)(meaning)
