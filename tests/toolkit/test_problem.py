"""Test binding a serialized Lean problem."""

import pytest
from sage.all import SR, exp, function, sqrt

from veriphy.core import CertificateError, ParamError, TableError
from veriphy.toolkit import Hyp, parse_symbolic, read_problem

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


SYMBOLIC = {
    'vars': ['x0', 'x1', 'x2'],
    'atoms': ['x / y', 'y', 'x'],
    'atom_types': ['ℝ', 'ℝ', 'ℝ'],
    'hyps': [
        {'expr': '(x1) - (0)', 'name': 'hy', 'poly': '(x1) - (0)', 'rel': 'ne', 'text': 'y ≠ 0'},
        {'expr': '(exp(x2)) - (1)', 'name': 'he', 'rel': 'le', 'text': 'Real.exp x ≤ 1'},
    ],
    'domain': [
        {'discharged_by': 'hy', 'expr': 'x1', 'kind': 'ne', 'text': 'y ≠ 0'},
        {'expr': 'x2', 'kind': 'pos', 'text': '0 < x'},
        {'expr': 'x1', 'kind': 'le', 'bound': 'x2', 'text': 'y ≤ x', 'discharged_by': 'hyx'},
    ],
    'goal': {'expr': '((x2 / x1)) - (sqrt(x2))', 'kind': 'other', 'rel': 'le', 'text': 'x / y ≤ √x'},
}


def test_read_problem_binds_symbolic_forms() -> None:
    """Bind symbolic forms of hypotheses and goals, with their relations, over symbolic variables."""
    bound = read_problem(SYMBOLIC)
    x1, x2 = bound.symbols['x1'], bound.symbols['x2']
    assert bound.hyps[0].expr == x1
    assert bound.hyps[1].poly is None
    assert bound.hyps[1].rel == 'le'
    assert bound.hyps[1].expr == exp(x2) - 1
    assert bound.goal.expr == x2 / x1 - sqrt(x2)
    assert bound.goal.rel == 'le'


def test_read_problem_binds_atom_types_and_domain() -> None:
    """Bind atom types and every domain condition kind, discharged or not."""
    bound = read_problem(SYMBOLIC)
    assert bound.atom_types == {'x0': 'ℝ', 'x1': 'ℝ', 'x2': 'ℝ'}
    assert [(c.kind, c.text, c.discharged_by) for c in bound.domain] == [
        ('ne', 'y ≠ 0', 'hy'),
        ('pos', '0 < x', None),
        ('le', 'y ≤ x', 'hyx'),
    ]
    assert bound.domain[2].bound == bound.symbols['x2']
    assert bound.domain[1].expr == bound.symbols['x2']
    assert bound.to_namespace()['domain'] is bound.domain


def test_read_problem_rejects_bad_domain_kind() -> None:
    """Reject a domain condition of unknown kind."""
    with pytest.raises(ParamError, match='bad domain condition'):
        read_problem({**SYMBOLIC, 'domain': [{'expr': 'x1', 'kind': 'odd', 'text': 'Odd y'}]})


def test_parse_symbolic_handles_sums_mod_and_matrices() -> None:
    """Parse range sums with bound variables, `mod`, matrix methods and unparseable text."""
    x0 = SR.var('x0')
    assert parse_symbolic('sum(k_, k_, 0, x0 - 1)', {'x0': x0}) == x0 * (x0 - 1) / 2
    assert str(parse_symbolic('mod(x0, 7)', {'x0': x0})) == 'mod(x0, 7)'
    assert parse_symbolic('(matrix(SR, [[1, x0], [0, 1]])).det()', {'x0': x0}) == 1
    assert parse_symbolic('((X)^(2)).subs(X=x0)', {'x0': x0}) == x0**2
    assert parse_symbolic('x0 +', {'x0': x0}) is None
    assert parse_symbolic(None, {}) is None


def test_read_problem_binds_namespaces_and_extensions() -> None:
    """Load the core, the packs the problem names and the project entries it carries, in that order."""
    extension = {'namespace': 'project', 'functions': [{'lean': 'Real.arcosh', 'sage': 'arccosh', 'arity': 1}]}
    bound = read_problem({**SYMBOLIC, 'namespaces': ['mathlib', 'physlib', 'project'], 'extensions': [extension]})
    assert [t.namespace for t in bound.tables] == ['mathlib', 'physlib', 'project']
    assert bound.tables[2].functions[0].sage == 'arccosh'


def test_read_problem_defaults_to_the_core_table() -> None:
    """Bind only the core table when the problem names no namespaces."""
    assert [t.namespace for t in read_problem(SYMBOLIC).tables] == ['mathlib']


def test_read_problem_rejects_an_unknown_pack() -> None:
    """Name the missing pack instead of rendering with the wrong table."""
    with pytest.raises(TableError, match=r'packs/nosuchlib\.json'):
        read_problem({**SYMBOLIC, 'namespaces': ['mathlib', 'nosuchlib']})


def test_read_problem_records_typed_sub_expressions() -> None:
    """Parse `typed` markers as their sub-expression, and record it with its Lean type."""
    goal = {'expr': "(typed(mod(x2, 7), 'ℕ') + x0) - (x0)", 'kind': 'other', 'rel': 'le', 'text': '↑(n % 7) + x ≤ x'}
    bound = read_problem({**SYMBOLIC, 'goal': goal})
    x2 = bound.symbols['x2']
    mod = function('mod', nargs=2)
    assert bound.typed == [(mod(x2, 7), 'ℕ')]
    assert bound.goal.expr == mod(x2, 7)
