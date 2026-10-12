"""Test the `run` method, which turns a proof script into Lean text."""

from collections.abc import Callable

from veriphy.core import JsonObject

Ok = Callable[..., JsonObject]
Err = Callable[..., str]

PROBLEM = {
    'vars': ['x0', 'x1'],
    'atoms': ['a', 'b'],
    'carrier': 'ℚ',
    'hyps': [{'name': 'h', 'poly': '(x0 + x1) - (3)', 'rel': 'eq', 'text': 'a + b = 3'}],
    'goal': {'kind': 'rel', 'poly': '(x0^2 + 2*x0*x1 + x1^2) - (9)', 'rel': 'eq', 'text': '(a + b) ^ 2 = 9'},
}


def test_answer_request_run_returns_lean(ok: Ok) -> None:
    """Return the block a script assigns, built with the pre-bound problem and toolkit."""
    script = "print('cofactor', x0 + x1 + 3)\nproof = linear_combination([(x0 + x1 + 3, hyp(problem, 'h'))], problem)"
    result = ok('run', problem=PROBLEM, script=script)
    assert result['lean'] == 'linear_combination (a + b + 3) * h'
    assert result['stdout'] == 'cofactor x0 + x1 + 3\n'


def test_answer_request_run_accepts_text(ok: Ok) -> None:
    """Accept a proof given as plain Lean text."""
    assert ok('run', problem=PROBLEM, script="proof = 'nlinarith [h]'")['lean'] == 'nlinarith [h]'


def test_answer_request_run_missing_proof(err: Err) -> None:
    """Report a script that assigns no proof, with its output."""
    error = err('run', problem=PROBLEM, script="print('searching')")
    assert 'did not assign `proof`' in error
    assert 'searching' in error


def test_answer_request_run_rejects_term(err: Err) -> None:
    """Reject a term where a tactic block is required."""
    assert 'must be a Lean tactic' in err('run', problem=PROBLEM, script="proof = hyp(problem, 'h')")


def test_answer_request_run_script_raises(err: Err) -> None:
    """Report an exception raised by the script, with its output."""
    error = err('run', problem=PROBLEM, script="print('step 1')\n1/0")
    assert 'ZeroDivisionError' in error
    assert 'step 1' in error


def test_answer_request_run_does_not_leak_assumptions(ok: Ok) -> None:
    """Forget assumptions a previous script made."""
    ok('run', problem=PROBLEM, script="t = var('t'); assume(t > 0); proof = 'trivial'")
    result = ok('run', problem=PROBLEM, script="t = var('t'); print(bool(t > 0)); proof = 'trivial'")
    assert result['stdout'] == 'False\n'
