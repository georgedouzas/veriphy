"""Test rendering symbolic expressions and building domain-aware steps."""

from collections.abc import Callable

import pytest
from sage.all import SR, I, abs_symbolic, cos, exp, gamma, log, matrix, pi, sin, sqrt, tan

from veriphy.core import CertificateError
from veriphy.toolkit import (
    Lean,
    field_simp_clearing,
    lemma_rewrite,
    matrix_term,
    read_problem,
    require_domain,
    steps,
    symbolic,
)

PROBLEM = read_problem(
    {
        'vars': ['x0', 'x1', 'x2', 'x3'],
        'atoms': ['x', 'z', 'k', 'n'],
        'atom_types': ['ℝ', 'ℂ', 'ℤ', 'ℕ'],
        'hyps': [{'name': 'hx', 'poly': '-x0', 'rel': 'lt', 'text': '0 < x'}],
        'domain': [
            {'expr': 'x0', 'kind': 'ne', 'text': 'x ≠ 0', 'discharged_by': 'hx'},
            {'expr': 'x0^2 + 1', 'kind': 'ne', 'text': 'x ^ 2 + 1 ≠ 0'},
            {'expr': 'x0 - 1', 'kind': 'pos', 'text': '0 < x - 1'},
        ],
        'goal': {'kind': 'false'},
    },
)
x, z, k, n = (PROBLEM.symbols[f'x{i}'] for i in range(4))


@pytest.mark.parametrize(
    ('function', 'name'),
    [(exp, 'exp'), (log, 'log'), (sin, 'sin'), (cos, 'cos'), (tan, 'tan')],
)
def test_function_table_dispatches_on_type(function: Callable[[object], object], name: str) -> None:
    """Render each table function as its `Real` version on reals and its `Complex` version on complex atoms."""
    assert str(symbolic(function(x), PROBLEM)) == f'Real.{name} x'
    assert str(symbolic(function(z), PROBLEM)) == f'Complex.{name} z'


def test_sqrt_is_real_only() -> None:
    """Render `sqrt` on reals, and reject it on complex atoms, since mathlib has no `Complex.sqrt`."""
    assert str(symbolic(sqrt(x), PROBLEM)) == 'Real.sqrt x'
    with pytest.raises(CertificateError, match=r"'sqrt' over ℂ.*\.veriphy/translations/"):
        symbolic(sqrt(z), PROBLEM)


def test_abs_renders_bars_on_every_type() -> None:
    """Render `abs` as `|·|` over ℝ, ℂ and ℤ, never `Int.natAbs`."""
    assert str(symbolic(abs_symbolic(x - 1), PROBLEM)) == '|x - 1|'
    assert str(symbolic(abs_symbolic(z), PROBLEM)) == '|z|'
    assert str(symbolic(abs_symbolic(k), PROBLEM)) == '|k|'


def test_constants_powers_and_quotients() -> None:
    """Render `pi`, `I`, natural and negative powers, `mod` and quotients."""
    assert str(symbolic(pi * x, PROBLEM)) == 'Real.pi * x'
    assert str(symbolic(I * z, PROBLEM)) == 'z * Complex.I'
    assert str(symbolic(x**n, PROBLEM)) == 'x ^ n'
    assert str(symbolic(1 / x**2, PROBLEM)) == '1 / x ^ 2'
    assert str(symbolic(x / (x**2 + 1) - SR(3) / 2, PROBLEM)) == 'x / (x ^ 2 + 1) - (3 / 2)'
    assert str(symbolic(SR(2) * k - 1, PROBLEM)) == '2 * k - 1'


def test_unmapped_function_is_rejected() -> None:
    """Reject a function outside the table, naming it."""
    with pytest.raises(CertificateError, match='gamma'):
        symbolic(gamma(x), PROBLEM)


def test_unknown_symbol_is_rejected() -> None:
    """Reject a symbol that is not an atom of the problem."""
    with pytest.raises(CertificateError, match="symbol 'w'"):
        symbolic(SR.var('w'), PROBLEM)


def test_require_domain_names_missing_conditions() -> None:
    """Fail naming every undischarged condition, and pass supplied proofs as facts."""
    with pytest.raises(CertificateError, match=r'x \^ 2 \+ 1 ≠ 0; 0 < x - 1'):
        require_domain(PROBLEM)
    names, haves = require_domain(PROBLEM, ('ne',), {'x ^ 2 + 1 ≠ 0': 'positivity'})
    assert names == ['hx', 'hd']
    assert [str(h) for h in haves] == ['have hd : x ^ 2 + 1 ≠ 0 := by positivity']


def test_field_simp_clearing_needs_denominator_facts() -> None:
    """Refuse to clear an undischarged denominator, and pass every denominator fact otherwise."""
    with pytest.raises(CertificateError, match=r'x \^ 2 \+ 1 ≠ 0'):
        field_simp_clearing(PROBLEM)
    step = field_simp_clearing(PROBLEM, {'x ^ 2 + 1 ≠ 0': 'positivity'})
    assert str(step).splitlines()[-1] == 'field_simp [hx, hd]'


def test_lemma_rewrite_passes_side_conditions() -> None:
    """Pass stated side conditions by name and supplied ones as `by` terms."""
    assert str(lemma_rewrite('Real.exp_add', PROBLEM, reverse=True)) == 'rw [← Real.exp_add]'
    rewrite = lemma_rewrite(
        'Real.log_div',
        PROBLEM,
        side=['x ≠ 0', 'x ^ 2 + 1 ≠ 0'],
        proofs={'x ^ 2 + 1 ≠ 0': 'positivity'},
    )
    assert str(rewrite) == 'rw [Real.log_div hx (by positivity)]'


def test_matrix_term_renders_literal() -> None:
    """Render a symbolic matrix as a `!![…]` literal."""
    assert str(matrix_term(matrix(SR, [[x, 1], [0, exp(x)]]), PROBLEM)) == '!![x, 1; 0, Real.exp x]'


def test_symbolic_emitters_parse_in_lean(lean_parses: Callable[[list[Lean]], str]) -> None:
    """Every symbolic emitter's output parses as Lean."""
    snippets = [
        symbolic(sqrt(x) / (x**2 + 1) + abs_symbolic(x - 1) * pi, PROBLEM),
        symbolic(exp(I * z) - log(z), PROBLEM),
        matrix_term(matrix(SR, [[x, 1], [0, 1 / x]]), PROBLEM),
        steps(field_simp_clearing(PROBLEM, {'x ^ 2 + 1 ≠ 0': 'positivity'}), lemma_rewrite('Real.exp_add', PROBLEM)),
    ]
    assert lean_parses(snippets) == ''
