"""Test Sage script sessions: `run_script` and `certify`."""

from collections.abc import Callable

from veriphy.core import JsonObject

Ok = Callable[..., JsonObject]
Err = Callable[..., str]

PROBLEM_INEQ = {
    'vars': ['x0', 'x1'],
    'atoms': ['x', 'y'],
    'hyps': [
        {'name': 'h1', 'poly': '(x0 + x1) - (1)', 'rel': 'le'},
        {'name': 'h2', 'poly': '(x0 - x1) - (3)', 'rel': 'eq'},
        {'name': 'h3', 'poly': '(0) - (x1)', 'rel': 'le'},
    ],
    'goal': {'kind': 'false'},
}

PROBLEM_EXISTS = {
    'vars': ['x0', 'x1'],
    'atoms': ['v₁', 'v₂'],
    'hyps': [],
    'goal': {
        'kind': 'exists',
        'binders': 2,
        'body': [{'poly': 'x0 + x1 - 1', 'rel': 'eq'}, {'poly': '0 - x0', 'rel': 'lt'}],
    },
}

PROBLEM_IDENTITY = {
    'vars': ['x0', 'x1'],
    'atoms': ['a', 'b'],
    'hyps': [
        {'name': 'h', 'poly': '(x0 + x1) - (3)', 'rel': 'eq'},
        {'name': "h'", 'poly': '(x0*x1) - (2)', 'rel': 'eq'},
    ],
    'goal': {'kind': 'rel', 'poly': '(x0^2 + x1^2) - (5)', 'rel': 'eq'},
}


def test_answer_request_run_script(ok: Ok) -> None:
    """Return the script's `results` exactly and its printed output."""
    result = ok('run_script', script="print('hi')\nresults = {'a': 1/3, 'b': [1, 2]}")
    assert set(result) == {'results', 'stdout', 'advisory'}
    assert result['results'] == {'a': '1/3', 'b': ['1', '2']}
    assert result['stdout'] == 'hi\n'


def test_answer_request_run_script_error_carries_stdout(err: Err) -> None:
    """Report a failing script with the output it printed first."""
    error = err('run_script', script="print('before')\n1/0")
    assert 'ZeroDivisionError' in error
    assert 'before' in error


def test_answer_request_certify_inequality(ok: Ok) -> None:
    """Return validated weights for a well-formed refutation, with the pre-bound problem visible."""
    script = (
        "assert [h.name for h in hyps] == ['h1', 'h2', 'h3']\n"
        "assert hyps[0].poly == x0 + x1 - 1 and hyps[0].rel == 'le'\n"
        "certificate = {'weights': {'h1': 1, 'h2': -1, 'h3': 2}}"
    )
    result = ok('certify', problem=PROBLEM_INEQ, family='inequality', script=script)
    weights = result['weights']
    assert isinstance(weights, list)
    assert [w['name'] for w in weights if isinstance(w, dict)] == ['h1', 'h2', 'h3']
    assert isinstance(weights[1], dict)
    assert weights[1]['poly'] == [{'coeff': '-1', 'exps': [0, 0]}]
    assert result['squares'] == []


def test_answer_request_certify_refutation_kappa(ok: Ok, err: Err) -> None:
    """Report the refuting constant, and reject a combination that is not constant."""
    result = ok(
        'certify',
        problem=PROBLEM_INEQ,
        family='inequality',
        script="certificate = {'h1': 1, 'h2': -1, 'h3': 2}",
    )
    assert (result['kappa'], result['strict']) == ('2', False)
    assert 'not constant' in err('certify', problem=PROBLEM_INEQ, family='inequality', script="certificate = {'h1': 1}")


def test_answer_request_certify_squares(ok: Ok) -> None:
    """Accept square terms for a relation goal."""
    problem = {
        'vars': ['x0', 'x1'],
        'atoms': ['a', 'b'],
        'hyps': [],
        'goal': {'kind': 'rel', 'poly': 'x0*x1 - (x0^2 + x1^2)/2', 'rel': 'le'},
    }
    result = ok('certify', problem=problem, family='inequality', script="certificate = {'squares': [(1/2, x0 - x1)]}")
    squares = result['squares']
    assert isinstance(squares, list)
    assert isinstance(squares[0], dict)
    assert squares[0]['coeff'] == '1/2'


def test_answer_request_certify_negative_weight(err: Err) -> None:
    """Reject a negative weight on an inequality hypothesis."""
    assert 'negative' in err('certify', problem=PROBLEM_INEQ, family='inequality', script="certificate = {'h1': -1}")


def test_answer_request_certify_missing_certificate(err: Err) -> None:
    """Report a script that assigns no certificate, with its output."""
    error = err('certify', problem=PROBLEM_INEQ, family='inequality', script="print('thinking')")
    assert 'did not assign `certificate`' in error
    assert 'thinking' in error


def test_answer_request_certify_unknown_hypothesis(err: Err) -> None:
    """Name an unknown hypothesis."""
    assert "'h9'" in err('certify', problem=PROBLEM_INEQ, family='inequality', script="certificate = {'h9': 1}")


def test_answer_request_certify_witness(ok: Ok, err: Err) -> None:
    """Return one rational per binder, and reject the wrong count."""
    result = ok('certify', problem=PROBLEM_EXISTS, family='witness', script='certificate = [QQ(1)/3, QQ(2)/3]')
    assert result['point'] == ['1/3', '2/3']
    error = err('certify', problem=PROBLEM_EXISTS, family='witness', script='certificate = [1]')
    assert '1 values for 2 binders' in error


def test_answer_request_certify_identity(ok: Ok) -> None:
    """Return the cofactors a script computes for an equality goal."""
    script = (
        'cs = goal.poly.lift(R.ideal([h.poly for h in hyps]))\n'
        "certificate = {'cofactors': {h.name: c for h, c in zip(hyps, cs)}}"
    )
    result = ok('certify', problem=PROBLEM_IDENTITY, family='identity', script=script)
    cofactors = result['cofactors']
    assert isinstance(cofactors, list)
    assert [c['name'] for c in cofactors if isinstance(c, dict)] == ['h', "h'"]


def test_answer_request_certify_script_raises(err: Err) -> None:
    """Report an exception raised by the script, with its output."""
    error = err('certify', problem=PROBLEM_INEQ, family='inequality', script="print('step 1')\n1/0")
    assert 'ZeroDivisionError' in error
    assert 'step 1' in error


def test_answer_request_certify_bad_family(err: Err) -> None:
    """Name `family` when it is not one of the three."""
    assert "'family'" in err('certify', problem=PROBLEM_INEQ, family='sum', script='')
