"""Test advisory Sage script sessions (`run_script`)."""

from collections.abc import Callable

from veriphy.core import JsonObject

Ok = Callable[..., JsonObject]
Err = Callable[..., str]


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
