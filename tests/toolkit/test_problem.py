"""Test binding a serialized Lean problem."""

import pytest

from veriphy.core import CertificateError, ParamError
from veriphy.toolkit import Hyp, read_problem

PROBLEM = {
    'vars': ['x0', 'x1'],
    'atoms': ['x', 'f a'],
    'hyps': [
        {'name': 'h', 'poly': '(x0) - (1)', 'rel': 'le', 'text': 'x ≤ 1'},
        {'name': 'hs', 'text': 'Real.sin x ≤ 1'},
    ],
    'goal': {'kind': 'other', 'text': 'Real.cos x ≤ 1'},
}


def test_read_problem_keeps_non_polynomial_hypotheses() -> None:
    """Keep a hypothesis without a polynomial form, with its text."""
    bound = read_problem(PROBLEM)
    assert bound.hyps[1] == Hyp('hs', None, None, 'Real.sin x ≤ 1')
    assert bound.hyps[0].rel == 'le'
    assert bound.atoms == {'x0': 'x', 'x1': 'f a'}


def test_read_problem_other_goal_has_text() -> None:
    """Bind a goal with no polynomial form by its text."""
    bound = read_problem(PROBLEM)
    assert bound.goal_kind == 'other'
    assert bound.goal is not None
    assert (bound.goal.poly, bound.goal.text) == (None, 'Real.cos x ≤ 1')


def test_read_problem_without_atoms() -> None:
    """Bind a problem with no atoms over a one-variable placeholder ring."""
    bound = read_problem({'vars': [], 'hyps': [], 'goal': {'kind': 'other', 'text': 'True'}})
    assert bound.ring.ngens() == 1


def test_read_problem_rejects_unknown_goal_kind() -> None:
    """Name the unknown goal kind."""
    with pytest.raises(ParamError, match='unknown goal kind'):
        read_problem({'vars': ['x0'], 'goal': {'kind': 'mystery'}})


def test_problem_find_hyp_checks_relation() -> None:
    """Reject a hypothesis whose relation the asking proof shape cannot use."""
    bound = read_problem(PROBLEM)
    assert bound.find_hyp('h', ('le',), 'farkas').name == 'h'
    with pytest.raises(CertificateError, match='not usable'):
        bound.find_hyp('hs', ('le',), 'farkas')


def test_problem_to_namespace_exposes_generators() -> None:
    """Expose the problem and each generator by name."""
    names = read_problem(PROBLEM).to_namespace()
    assert names['problem'] is not None
    assert str(names['x0']) == 'x0'
