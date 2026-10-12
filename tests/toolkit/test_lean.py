"""Test Lean values and rendering over atoms."""

from collections.abc import Callable

import pytest
from sage.all import QQ

from veriphy.core import VeriphyError
from veriphy.toolkit import Lean, parenthesize, polynomial, rational, read_problem, tactic, term

PROBLEM = read_problem({'vars': ['x0', 'x1'], 'atoms': ['f a', 'v₁'], 'goal': {'kind': 'false'}})


def test_lean_rejects_unknown_kind() -> None:
    """Reject a syntactic category other than term and tactic."""
    with pytest.raises(VeriphyError, match='kind'):
        Lean('x', 'command')


def test_parenthesize_atoms() -> None:
    """Leave identifiers and numerals bare, wrap everything else."""
    assert [parenthesize(t) for t in ('x', "x'", 'Nat.succ', '12', 'f a', 'x + 1')] == [
        'x',
        "x'",
        'Nat.succ',
        '12',
        '(f a)',
        '(x + 1)',
    ]


def test_rational_signs() -> None:
    """Render signs and fractions exactly."""
    assert [str(rational(q)) for q in (0, 5, -5, QQ(1) / 3, QQ(-7) / 2)] == ['0', '5', '-5', '1 / 3', '-(7 / 2)']


def test_polynomial_over_atoms() -> None:
    """Render monomials over the atoms' text, with signs between terms."""
    assert str(polynomial('-x0^2*x1 + 3*x1 - 1/2', PROBLEM)) == '-(f a) ^ 2 * v₁ + 3 * v₁ - 1 / 2'
    assert str(polynomial(0, PROBLEM)) == '0'
    assert str(polynomial('-1', PROBLEM)) == '-1'


def test_polynomial_parses_in_lean(lean_parses: Callable[[list[Lean]], str]) -> None:
    """Parse every rendered form as a Lean term."""
    snippets = [polynomial(p, PROBLEM) for p in ('-x0^2*x1 + 3*x1 - 1/2', '-x0/7', 'x0*x1 - x1^3')]
    snippets += [rational(QQ(-3) / 4), term('h1'), tactic('norm_num')]
    assert lean_parses(snippets) == ''


def test_lean_parses_detects_errors(lean_parses: Callable[[list[Lean]], str]) -> None:
    """Report text that does not parse."""
    assert lean_parses([term('(1 +')]) != ''
