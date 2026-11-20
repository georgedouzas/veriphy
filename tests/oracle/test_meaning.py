"""Test the daemon's meaning check on claims serialized by `#veriphy_meaning`."""

import json
from collections.abc import Callable
from pathlib import Path

import pytest

from veriphy.core import JsonObject

Ok = Callable[..., JsonObject]
Err = Callable[..., str]
PROBLEMS = json.loads((Path(__file__).parent / 'fixtures' / 'meaning_problems.json').read_text())


def test_meaning_finds_a_wrong_formalization(ok: Ok) -> None:
    """Refute `∀ x, 0 ≤ x → √(x²) = -x` at a value, with both sides."""
    result = ok('meaning', problem=PROBLEMS['wrong'], seed=0, values=10)
    assert result['outcome'] == 'counterexample'
    counterexample = result['counterexample']
    assert isinstance(counterexample, dict)
    assert counterexample['values'] == {'x': '1'}
    assert (counterexample['lhs'], counterexample['rhs']) == ('1', '-1')


def test_meaning_agrees_with_a_faithful_formalization(ok: Ok) -> None:
    """Agree with `∀ x, √(x²) = |x|` at ten drawn values: with its domain condition not discharged, it is sampled."""
    result = ok('meaning', problem=PROBLEMS['faithful'], seed=0, values=10)
    assert (result['outcome'], result['method'], result['agreed']) == ('agrees', 'sampled', 10)
    assert result['note'] is None


def test_meaning_is_undecided_on_narrow_hypotheses(ok: Ok) -> None:
    """Name the hypothesis `x = π`, which no drawn rational satisfies."""
    result = ok('meaning', problem=PROBLEMS['narrow'], seed=0, values=10)
    assert result['outcome'] == 'undecided'
    assert 'x = Real.pi' in str(result['reason'])
    assert result['draws'] == 200
    rejected = result['rejected']
    assert isinstance(rejected, dict)
    assert list(rejected) == ['hyp0: x = Real.pi']


def test_meaning_at_given_points(ok: Ok) -> None:
    """Evaluate at the values the caller gives, exactly: `sin π = 0` at `x = π`."""
    result = ok('meaning', problem=PROBLEMS['narrow'], seed=0, values=10, points=[{'x': 'pi'}])
    assert (result['outcome'], result['agreed'], result['values']) == ('agrees', 1, [{'x': 'pi'}])


def test_meaning_rejects_points_missing_a_binder(err: Err) -> None:
    """Refuse a point that does not name every binder."""
    assert 'each point names every binder' in err('meaning', problem=PROBLEMS['narrow'], points=[{'y': '1'}])


@pytest.mark.parametrize('name', ['faithful', 'natsub'])
def test_meaning_same_seed_same_values(ok: Ok, name: str) -> None:
    """Draw the same values for the same seed, and others for another seed."""
    first, again, other = (ok('meaning', problem=PROBLEMS[name], seed=s, values=10) for s in (3, 3, 4))
    assert first == again
    assert first.get('values') != other.get('values') or first.get('counterexample') != other.get('counterexample')


def test_meaning_identity_agrees_symbolically(ok: Ok) -> None:
    """Decide `cos² x + sin² x = 1` symbolically, with no values drawn."""
    result = ok('meaning', problem=PROBLEMS['trig'], seed=0, values=10)
    assert (result['outcome'], result['method']) == ('agrees', 'symbolic')
    assert 'values' not in result


def test_meaning_undecided_identity_falls_back_to_sampling(ok: Ok) -> None:
    """Fall back to sampling when the identity does not simplify, and find ℕ subtraction's truncation."""
    result = ok('meaning', problem=PROBLEMS['natsub'], seed=0, values=10)
    assert (result['outcome'], result['method']) == ('counterexample', 'sampled')
    counterexample = result['counterexample']
    assert isinstance(counterexample, dict)
    values = counterexample['values']
    assert isinstance(values, dict)
    assert int(str(values['m'])) > int(str(values['n']))


def test_meaning_notes_untested_junk_values(ok: Ok) -> None:
    """Agree with `x / x = 1` away from zero, and say that `x = 0`, where Lean's value is junk, went untested."""
    result = ok('meaning', problem=PROBLEMS['divx'], seed=0, values=10)
    assert (result['outcome'], result['method']) == ('agrees', 'sampled')
    assert result['rejected'] == {'domain: x ≠ 0': 1}
    assert 'x ≠ 0' in str(result['note'])
