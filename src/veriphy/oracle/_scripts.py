"""Run Sage scripts: advisory derivation sessions and agent-written certificates."""

import contextlib
import io
import signal
from collections.abc import Iterator
from types import FrameType

import sage.all as sage_all
from sage.all import QQ
from sage.repl.preparse import preparse_file
from sage.rings.polynomial.multi_polynomial import MPolynomial
from sage.rings.polynomial.multi_polynomial_ring_base import MPolynomialRing_base
from sage.rings.rational import Rational

import veriphy.toolkit
from veriphy.core import CertificateError, Method, ParamError, ScriptError
from veriphy.oracle._registry import (
    _coerce_int,
    _coerce_json,
    _coerce_str,
    _register_method,
)
from veriphy.toolkit import Lean, Problem, read_problem

SCRIPT_METHODS: dict[str, Method] = {}
STDOUT_LIMIT = 20000
DEFAULT_TIMEOUT_S = 120
FAMILIES = ('identity', 'inequality', 'witness')
SQUARE_ARITY = 2


def _truncate(out: str) -> str:
    """Return script output cut to `STDOUT_LIMIT` characters, noting how much was dropped."""
    if len(out) <= STDOUT_LIMIT:
        return out
    return out[:STDOUT_LIMIT] + f'\n...[truncated {len(out) - STDOUT_LIMIT} chars]'


@contextlib.contextmanager
def _alarm(timeout: int) -> Iterator[None]:
    """Bound the enclosed block by `timeout` seconds of wall clock, raising `TimeoutError` past it."""

    def on_alarm(_signum: int, _frame: FrameType | None) -> None:
        """Raise the timeout inside the running script."""
        message = f'script exceeded {timeout}s'
        raise TimeoutError(message)

    previous = signal.signal(signal.SIGALRM, on_alarm)
    signal.alarm(timeout)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, previous)


def _run_sage(script: str, namespace: dict[str, object], timeout: int) -> str:
    """Run preparsed Sage source in `namespace` over `sage.all`, the caller's names shadowing Sage's."""
    prebound = dict(namespace)
    namespace.update({k: v for k, v in vars(sage_all).items() if not k.startswith('_')})
    namespace.update(prebound)
    code = compile(preparse_file(script), '<veriphy-script>', 'exec')
    buffer = io.StringIO()
    try:
        with _alarm(timeout), contextlib.redirect_stdout(buffer):
            exec(code, namespace)  # noqa: S102 - running the caller's script is the method # nosec B102
    except Exception as exc:
        reason = f'{type(exc).__name__}: {exc}'
        raise ScriptError(reason, _truncate(buffer.getvalue())) from exc
    finally:
        sage_all.forget()
    return _truncate(buffer.getvalue())


@_register_method(
    SCRIPT_METHODS,
    'run_script',
    advisory=True,
    script=_coerce_str,
    timeout_s=_coerce_int(DEFAULT_TIMEOUT_S),
)
def _run_derivation(script: str, timeout_s: int) -> dict[str, object]:
    """Run a whole Sage derivation script and return its `results` and printed output, as guidance only."""
    namespace: dict[str, object] = {}
    out = _run_sage(script, namespace, timeout_s)
    return {'results': namespace.get('results'), 'stdout': out, 'advisory': True}


def _toolkit_names() -> dict[str, object]:
    """Return the toolkit's public names, which every proof script sees."""
    return {name: getattr(veriphy.toolkit, name) for name in veriphy.toolkit.__all__}


def _read_proof(namespace: dict[str, object], out: str) -> str:
    """Return the Lean tactic block a script assigned to `proof`."""
    if namespace.get('proof') is None:
        message = 'the script did not assign `proof` (a Lean tactic block, as text or a toolkit `Lean` value)'
        raise ScriptError(message, out)
    proof = namespace['proof']
    if isinstance(proof, Lean):
        if proof.kind != 'tactic':
            message = f'`proof` must be a Lean tactic, got a {proof.kind}: {proof.text}'
            raise ScriptError(message, out)
        return proof.text
    if isinstance(proof, str):
        return proof
    message = f'`proof` must be Lean text or a toolkit `Lean` value, got {type(proof).__name__}'
    raise ScriptError(message, out)


@_register_method(
    SCRIPT_METHODS,
    'run',
    problem=_coerce_json,
    script=_coerce_str,
    timeout_s=_coerce_int(DEFAULT_TIMEOUT_S),
)
def _run_proof_script(problem: object, script: str, timeout_s: int) -> dict[str, object]:
    """Return the Lean tactic block a proof script builds, with the problem and the toolkit pre-bound."""
    namespace = {**_toolkit_names(), **read_problem(problem).to_namespace(), 'proof': None}
    out = _run_sage(script, namespace, timeout_s)
    return {'lean': _read_proof(namespace, out), 'stdout': out}


def _to_rational(v: object, what: str) -> Rational:
    """Return `v` as an exact rational, or raise naming `what`."""
    try:
        return QQ(v)
    except (TypeError, ValueError, ArithmeticError) as exc:
        message = f'{what}: {v!r} is not an exact rational'
        raise CertificateError(message) from exc


def _to_poly(ring: MPolynomialRing_base, v: object, what: str) -> MPolynomial:
    """Return `v` as a polynomial of `ring`, or raise naming `what`."""
    try:
        return ring(v)
    except (TypeError, ValueError, ArithmeticError) as exc:
        message = f'{what}: {v!r} is not a polynomial in {ring}'
        raise CertificateError(message) from exc


def _validate_identity(cert: object, problem: Problem) -> dict[str, object]:
    """Return an identity certificate normalized to `{'cofactors': [{name, poly}]}`."""
    if problem.goal_kind != 'rel' or problem.goal is None or problem.goal.rel != 'eq':
        message = 'identity needs an equality goal'
        raise CertificateError(message)
    cofactors = cert.get('cofactors', cert) if isinstance(cert, dict) else None
    if not isinstance(cofactors, dict):
        message = "identity certificate must be {'cofactors': {hyp_name: polynomial}}"
        raise CertificateError(message)
    out = []
    for name, c in cofactors.items():
        problem.find_hyp(name, ('eq',), 'identity')
        poly = _to_poly(problem.ring, c, f'cofactor of {name}')
        if poly != 0:
            out.append({'name': name, 'poly': poly})
    return {'cofactors': out}


def _split_inequality(cert: object) -> tuple[dict[str, object], list[object]]:
    """Return the weights and squares of an inequality certificate, accepting the bare-weights shorthand."""
    if isinstance(cert, dict) and ('weights' in cert or 'squares' in cert):
        return cert.get('weights', {}), cert.get('squares', [])
    if isinstance(cert, dict):
        return cert, []
    message = "inequality certificate must be {'weights': {...}, 'squares': [(c, q), ...]}"
    raise CertificateError(message)


def _read_weight(name: str, w: object, problem: Problem) -> MPolynomial:
    """Return one hypothesis weight: any polynomial on an equality, a nonnegative rational on an inequality."""
    hyp = problem.find_hyp(name, ('eq', 'le', 'lt'), 'inequality')
    if hyp.rel == 'eq':
        return _to_poly(problem.ring, w, f'weight of {name}')
    q = _to_rational(w, f'weight of {name}')
    if q < 0:
        message = f"weight of inequality hypothesis '{name}' is negative ({q})"
        raise CertificateError(message)
    return problem.ring(q)


def _read_square(i: int, sq: object, ring: MPolynomialRing_base) -> tuple[Rational, MPolynomial]:
    """Return one `(coefficient, polynomial)` square term, checking the coefficient is nonnegative."""
    if not isinstance(sq, list | tuple) or len(sq) != SQUARE_ARITY:
        message = f'square {i} must be a pair (coefficient, polynomial)'
        raise CertificateError(message)
    c = _to_rational(sq[0], f'square {i} coefficient')
    if c < 0:
        message = f'square {i} has a negative coefficient ({c})'
        raise CertificateError(message)
    return c, _to_poly(ring, sq[1], f'square {i}')


def _find_refutation_constant(
    weights: list[tuple[str, MPolynomial]],
    squares: list[tuple[Rational, MPolynomial]],
    problem: Problem,
) -> tuple[Rational, bool]:
    """Return the constant a refuting combination reduces to and whether it uses a strict hypothesis."""
    by_name = {h.name: h for h in problem.hyps}
    combo = sum((w * by_name[name].poly for name, w in weights), problem.ring.zero())
    combo += sum((c * q**2 for c, q in squares), problem.ring.zero())
    if combo.degree() > 0:
        message = f'the weighted combination is not constant: {combo}'
        raise CertificateError(message)
    kappa = QQ(combo.constant_coefficient())
    strict = any(by_name[name].rel == 'lt' for name, _ in weights)
    if not (kappa > 0 or (kappa == 0 and strict)):
        message = f'the weighted combination gives κ = {kappa}, which is not contradictory'
        raise CertificateError(message)
    return kappa, strict


def _validate_inequality(cert: object, problem: Problem) -> dict[str, object]:
    """Return an inequality certificate normalized to weights and squares, plus `kappa` for a `False` goal."""
    raw_weights, raw_squares = _split_inequality(cert)
    weights = [(name, _read_weight(name, w, problem)) for name, w in raw_weights.items()]
    weights = [(name, w) for name, w in weights if w != 0]
    squares = [_read_square(i, sq, problem.ring) for i, sq in enumerate(raw_squares)]
    squares = [(c, q) for c, q in squares if c != 0 and q != 0]
    if not weights and not squares:
        message = 'inequality certificate is empty (every weight is zero)'
        raise CertificateError(message)
    out: dict[str, object] = {
        'weights': [{'name': name, 'poly': w} for name, w in weights],
        'squares': [{'coeff': c, 'terms': q} for c, q in squares],
    }
    if problem.goal_kind == 'false':
        kappa, strict = _find_refutation_constant(weights, squares, problem)
        out.update({'kappa': kappa, 'strict': strict})
    return out


def _validate_witness(cert: object, problem: Problem) -> dict[str, object]:
    """Return a witness certificate normalized to `{'point': [...]}`, one rational per binder."""
    if problem.goal_kind != 'exists':
        message = 'witness needs an existential goal'
        raise CertificateError(message)
    point = cert.get('point') if isinstance(cert, dict) else cert
    if not isinstance(point, list | tuple):
        message = 'witness certificate must be a list of rationals, one per binder'
        raise CertificateError(message)
    if len(point) != len(problem.binders):
        message = f'witness has {len(point)} values for {len(problem.binders)} binders'
        raise CertificateError(message)
    return {'point': [_to_rational(v, f'witness value {i}') for i, v in enumerate(point)]}


def _validate_certificate(family: str, cert: object, problem: Problem) -> dict[str, object]:
    """Return a script's `certificate` normalized to the schema of `family`."""
    if family == 'identity':
        return _validate_identity(cert, problem)
    if family == 'inequality':
        return _validate_inequality(cert, problem)
    return _validate_witness(cert, problem)


@_register_method(
    SCRIPT_METHODS,
    'certify',
    problem=_coerce_json,
    family=_coerce_str,
    script=_coerce_str,
    timeout_s=_coerce_int(DEFAULT_TIMEOUT_S),
)
def _certify_script(problem: object, family: str, script: str, timeout_s: int) -> dict[str, object]:
    """Return the validated `certificate` an agent-written script assigns, with the Lean problem pre-bound."""
    if family not in FAMILIES:
        raise ParamError(param='family', reason=f'must be one of {list(FAMILIES)}')
    bound = read_problem(problem)
    namespace = bound.to_namespace()
    out = _run_sage(script, namespace, timeout_s)
    if 'certificate' not in namespace:
        message = 'the script did not assign `certificate`'
        raise ScriptError(message, out)
    try:
        return _validate_certificate(family, namespace['certificate'], bound)
    except CertificateError as exc:
        raise ScriptError(str(exc), out) from exc
