"""Decide symbolic and matrix identities and solve equation systems, as advisory guidance."""

import contextlib
import secrets
from collections.abc import Callable, Iterator, Sequence

from sage.all import CDF, SR, assume, forget, matrix, sage_eval, solve, var
from sage.symbolic.expression import Expression

from veriphy.core import JsonObject, JsonValue, Method, ParamError, VeriphyError
from veriphy.oracle._registry import _get_param, _register_method

SYMBOLIC_METHODS: dict[str, Method] = {}
DEFAULT_SAMPLES = 20
RESAMPLE_FACTOR = 10
SAMPLE_RANGE = 10.0
TOLERANCE = 1e-8
SAMPLER = secrets.SystemRandom()

Evaluate = Callable[[dict[Expression, float]], float]


def _check_names(names: object) -> list[str]:
    """Return the declared variable names, rejecting anything that is not a list of identifiers."""
    if not isinstance(names, list) or not all(isinstance(n, str) and n.isidentifier() for n in names):
        raise ParamError(param='vars', reason='must be a list of identifiers')
    return names


def _parse_symbolic(strs: Sequence[object], names: list[str]) -> list[Expression]:
    """Return expression strings parsed in the symbolic ring over the declared variables."""
    if not names:
        raise ParamError(param='vars', reason='must be a non-empty list of identifiers')
    scope = {n: var(n) for n in names}
    return [sage_eval(str(s), locals=scope) for s in strs]


@contextlib.contextmanager
def _assuming(assumptions: list[Expression]) -> Iterator[None]:
    """Hold the symbolic assumptions for the enclosed block and forget them afterwards."""
    try:
        for a in assumptions:
            assume(a)
        yield
    finally:
        forget()


def _sample_point(names: list[str]) -> dict[Expression, float]:
    """Return a random real point for the declared variables."""
    return {var(v): SAMPLER.uniform(-SAMPLE_RANGE, SAMPLE_RANGE) for v in names}


def _sample_difference(names: list[str], evaluate: Evaluate, samples: int) -> JsonObject:
    """Return the numeric verdict on a difference: a counterexample, or undecided after `samples` points."""
    tried = 0
    for _ in range(RESAMPLE_FACTOR * samples):
        if tried >= samples:
            break
        point = _sample_point(names)
        try:
            worst = evaluate(point)
        except (ValueError, TypeError, ZeroDivisionError, ArithmeticError):
            continue
        tried += 1
        if worst > TOLERANCE:
            return {
                'equal': False,
                'method': 'numeric',
                'advisory': True,
                'counterexample': {str(v): float(x) for v, x in point.items()},
                'difference': str(worst),
            }
    if tried == 0:
        message = 'no sample point evaluated successfully'
        raise VeriphyError(message)
    return {
        'equal': None,
        'method': 'numeric',
        'advisory': True,
        'note': f'undecided symbolically; {tried} random samples found no counterexample',
    }


@_register_method(SYMBOLIC_METHODS, 'symbolic_check', advisory=True, raw=True)
def _check_symbolic_identity(params: JsonObject) -> JsonObject:
    """Return whether `lhs == rhs` holds symbolically, falling back to numeric sampling, as guidance only."""
    names = _check_names(params.get('vars'))
    lhs, rhs = _parse_symbolic([_get_param('lhs', params), _get_param('rhs', params)], names)
    assumptions = _parse_symbolic(_as_list(params.get('assumptions', [])), names)
    with _assuming(assumptions):
        if (lhs - rhs).simplify_full().is_zero():
            return {'equal': True, 'method': 'symbolic', 'advisory': True}
        return _sample_difference(
            names,
            lambda point: abs(CDF((lhs - rhs).subs(point))),
            int(str(params.get('samples', DEFAULT_SAMPLES))),
        )


def _as_list(value: object) -> list[object]:
    """Return a list parameter, or an empty list for anything else."""
    return value if isinstance(value, list) else []


@_register_method(SYMBOLIC_METHODS, 'solve', advisory=True, raw=True)
def _solve_system(params: JsonObject) -> JsonObject:
    """Return the symbolic solutions of an equation system as `{var: expression}` dicts, as guidance only."""
    names = _check_names(params.get('vars'))
    parsed = _parse_symbolic(_as_list(_get_param('equations', params)), names)
    equations = [e if e.is_relational() else (e == 0) for e in parsed]
    unknowns = [var(str(v)) for v in _as_list(params.get('solve_for', names))]
    solutions = solve(equations, unknowns, solution_dict=True)
    return {'solutions': [{str(v): str(e) for v, e in s.items()} for s in solutions], 'advisory': True}


def _load_matrices(params: JsonObject, names: list[str]) -> dict[str, object]:
    """Return the evaluation scope: the declared variables plus each named matrix over the symbolic ring."""
    scope: dict[str, object] = {n: var(n) for n in names}
    matrices = params.get('matrices', {})
    named: dict[str, JsonValue] = matrices if isinstance(matrices, dict) else {}
    for mname, rows in named.items():
        if not mname.isidentifier():
            raise ParamError(param='matrices', reason=f'matrix name {mname!r} is not a valid identifier')
        entries = [[sage_eval(str(e), locals=dict(scope)) for e in _as_list(row)] for row in _as_list(rows)]
        scope[mname] = matrix(SR, entries)
    return scope


@_register_method(SYMBOLIC_METHODS, 'matrix_check', advisory=True, raw=True)
def _check_matrix_identity(params: JsonObject) -> JsonObject:
    """Return whether a matrix-valued (or scalar) identity holds, entry by entry, as guidance only."""
    names = _check_names(params.get('vars', []))
    scope = _load_matrices(params, names)
    lhs = sage_eval(str(_get_param('lhs', params)), locals=dict(scope))
    rhs = sage_eval(str(_get_param('rhs', params)), locals=dict(scope))
    assumptions = _parse_symbolic(_as_list(params.get('assumptions', [])), names) if names else []
    diff = lhs - rhs
    entries = list(diff.list()) if hasattr(diff, 'nrows') else [SR(diff)]
    with _assuming(assumptions):
        if all(SR(e).simplify_full().is_zero() for e in entries):
            return {'equal': True, 'method': 'symbolic', 'advisory': True}
        if not names:
            message = 'entries did not simplify to zero and there are no vars to sample'
            raise VeriphyError(message)
        verdict = _sample_difference(
            names,
            lambda point: max(abs(CDF(SR(e).subs(point))) for e in entries),
            int(str(params.get('samples', DEFAULT_SAMPLES))),
        )
    if 'difference' in verdict:
        verdict['max_entry_difference'] = verdict.pop('difference')
    return verdict
