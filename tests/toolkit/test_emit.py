"""Test the Lean proof-step emitters."""

from collections.abc import Callable

import pytest
from sage.all import QQ

from veriphy.core import CertificateError, VeriphyError
from veriphy.toolkit import (
    Lean,
    by_cases,
    calc_chain,
    combination,
    decide,
    field_simp,
    fresh_name,
    hyp,
    linear_combination,
    mul_nonneg,
    mul_pos,
    negate_goal,
    nlinarith,
    norm_num,
    positivity,
    rcases,
    read_problem,
    refute,
    rewrite_by,
    sq_nonneg,
    steps,
    sum_by_induction,
    tactic,
    term,
    witness,
)

PROBLEM = read_problem(
    {
        'vars': ['x0', 'x1'],
        'atoms': ['a', 'f b'],
        'carrier': 'ℚ',
        'hyps': [{'name': 'h', 'poly': 'x0 - 1', 'rel': 'le', 'text': 'a ≤ 1'}, {'name': 'h_1', 'text': 'True'}],
        'goal': {'kind': 'false'},
    },
)


def test_fresh_name_skips_taken_names() -> None:
    """Skip names the problem or the caller already uses."""
    assert fresh_name(PROBLEM, 'h') == 'h_2'
    assert fresh_name(PROBLEM, 'k', taken=['k']) == 'k_1'


def test_hyp_rejects_unknown_names() -> None:
    """Name the unknown hypothesis and the known ones."""
    with pytest.raises(CertificateError, match=r"'h9'.*known"):
        hyp(PROBLEM, 'h9')


def test_combination_rejects_all_zero_weights() -> None:
    """Refuse to build an empty combination."""
    with pytest.raises(CertificateError, match='empty'):
        combination([(0, term('h'))], PROBLEM)


def test_emitters_reject_wrong_categories() -> None:
    """Reject a term where a tactic is required, and the other way round."""
    with pytest.raises(VeriphyError, match='tactic'):
        steps(term('h'))
    with pytest.raises(VeriphyError, match='term'):
        nlinarith([tactic('ring')])


def test_rcases_counts_branches() -> None:
    """Reject mismatched names and branches."""
    with pytest.raises(VeriphyError, match='names'):
        rcases(term('h'), ['a', 'b'], [tactic('simp')])


def test_refute_needs_carrier() -> None:
    """Refuse to state the constant without a carrier type."""
    bare = read_problem({'vars': ['x0'], 'goal': {'kind': 'false'}})
    with pytest.raises(VeriphyError, match='carrier'):
        refute(1, strict=False, weighted=[(1, term('h'))], problem=bare)


def test_emitted_text_is_unhygienic() -> None:
    """Emit no hygiene markers."""
    block = steps(
        negate_goal(fresh_name(PROBLEM, 'h')),
        refute(QQ(1), strict=True, weighted=[(1, hyp(PROBLEM, 'h'))], problem=PROBLEM),
    )
    assert '✝' not in block.text


def test_emitters_parse_in_lean(lean_parses: Callable[[list[Lean]], str]) -> None:
    """Parse the output of every builder in its category."""
    snippets = [
        hyp(PROBLEM, 'h'),
        combination([(QQ(1) / 3, term('h')), ('x0 - x1', term('h'))], PROBLEM),
        linear_combination([(2, term('h'))], PROBLEM),
        sq_nonneg('x0 - x1', PROBLEM),
        mul_nonneg(term('h'), sq_nonneg('x1', PROBLEM)),
        mul_pos(term('h'), term('h')),
        nlinarith([sq_nonneg('x0*x1 - 1', PROBLEM)]),
        nlinarith(),
        positivity(),
        field_simp(['h']),
        norm_num(['h'], at='h'),
        decide(),
        rewrite_by('x0^2 - 1', term('(a - 1) * (a + 1)'), tactic('ring1'), PROBLEM),
        calc_chain(
            term('(a + 1) ^ 2'),
            [('=', 'x0^2 + 2*x0 + 1', tactic('ring')), ('≤', 'x0^2 + 2*x0 + 2', tactic('linarith'))],
            PROBLEM,
        ),
        by_cases('hx', term('a ≤ 0'), steps(tactic('intro'), nlinarith()), positivity()),
        rcases(term('le_or_lt a 0'), ['hx', 'hx'], [nlinarith(), positivity()]),
        witness([1, QQ(-1) / 2], norm_num()),
        negate_goal('hneg'),
        refute(2, strict=False, weighted=[(1, term('h')), (-1, term('h'))], problem=PROBLEM),
        sum_by_induction('n'),
        steps(tactic('intro x'), positivity()),
    ]
    assert lean_parses(snippets) == ''
