"""Run Sage scripts: advisory derivation sessions and agent-written certificates."""

import contextlib
import io
import signal
from collections.abc import Iterator
from types import FrameType

import sage.all as sage_all
from sage.repl.preparse import preparse_file

import veriphy.toolkit
from veriphy.core import CertificateError, Method, ScriptError
from veriphy.oracle._registry import (
    _coerce_int,
    _coerce_json,
    _coerce_str,
    _register_method,
)
from veriphy.toolkit import Lean, check_instances, read_problem

SCRIPT_METHODS: dict[str, Method] = {}
STDOUT_LIMIT = 20000
DEFAULT_TIMEOUT_S = 120


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


def _read_proof(namespace: dict[str, object], out: str) -> tuple[str, bool]:
    """Return the Lean tactic block a script assigned to `proof`, and whether it leaves goals open on purpose."""
    if namespace.get('proof') is None:
        message = 'the script did not assign `proof` (a Lean tactic block, as text or a toolkit `Lean` value)'
        raise ScriptError(message, out)
    proof = namespace['proof']
    if isinstance(proof, Lean):
        if proof.kind != 'tactic':
            message = f'`proof` must be a Lean tactic, got a {proof.kind}: {proof.text}'
            raise ScriptError(message, out)
        return proof.text, proof.leaves_goals
    if isinstance(proof, str):
        return proof, False
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
    lean, leaves_goals = _read_proof(namespace, out)
    return {'lean': lean, 'stdout': out, 'leaves_goals': leaves_goals}


def run_test_script(problem: object, script: str, timeout_s: int) -> dict[str, object]:
    """Return the instances a test script chooses for a claim's universal binders, with its seed and Sage's version.

    This is the daemon's `test` method; the test catalog calls it to rerun a record's oracle instances.

    Args:
        problem: The serialized problem of the claim.
        script: The test script.
        timeout_s: The script's time limit.

    Returns:
        The instances, the script's output, its seed and Sage's version.

    Raises:
        ScriptError: If the script fails, assigns no `instances`, or an instance is malformed.
    """
    read = read_problem(problem)
    namespace = {**_toolkit_names(), **read.to_namespace(), 'instances': None, 'SEED': 0}
    out = _run_sage(script, namespace, timeout_s)
    if namespace.get('instances') is None:
        message = 'the script did not assign `instances` (a list of kernel_instance and oracle_instance values)'
        raise ScriptError(message, out)
    chosen = namespace['instances']
    if not isinstance(chosen, list | tuple):
        message = '`instances` must be a list'
        raise ScriptError(message, out)
    try:
        checked = check_instances(chosen, len(read.universal))
    except CertificateError as exc:
        raise ScriptError(str(exc), out) from exc
    seed = namespace.get('SEED', 0)
    return {
        'instances': [i.to_json() for i in checked],
        'stdout': out,
        'seed': int(seed) if isinstance(seed, int) else 0,
        'sage_version': str(sage_all.version()),
    }


# the daemon method wraps the plain function, which the test catalog also calls
_register_method(
    SCRIPT_METHODS,
    'test',
    problem=_coerce_json,
    script=_coerce_str,
    timeout_s=_coerce_int(DEFAULT_TIMEOUT_S),
)(run_test_script)
