"""Test rendering symbolic expressions and building domain-aware steps."""

from collections.abc import Callable

import pytest
from sage.all import (
    SR,
    I,
    abs_symbolic,
    arccos,
    arcsin,
    arctan,
    ceil,
    cos,
    cosh,
    exp,
    factorial,
    floor,
    gamma,
    log,
    matrix,
    pi,
    sin,
    sinh,
    sqrt,
    tan,
    tanh,
)

from veriphy.core import CertificateError
from veriphy.toolkit import (
    Lean,
    Problem,
    field_simp_clearing,
    lemma_rewrite,
    matrix_term,
    read_problem,
    require_domain,
    rewrite_candidates,
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


TYPED = read_problem(
    {
        'vars': ['x0', 'x1', 'x2'],
        'atoms': ['x', 'n', 'k'],
        'atom_types': ['ℝ', 'ℕ', 'ℤ'],
        'carrier': 'ℝ',
        'goal': {'expr': "(typed(mod(x1, 7), 'ℕ') + x0) - (x0)", 'kind': 'other', 'rel': 'le', 'text': ''},
    },
)
xr, nn, kk = (TYPED.symbols[f'x{i}'] for i in range(3))


@pytest.mark.parametrize(
    ('function', 'lean'),
    [
        (cosh, 'Real.cosh'),
        (sinh, 'Real.sinh'),
        (tanh, 'Real.tanh'),
        (arctan, 'Real.arctan'),
        (arcsin, 'Real.arcsin'),
        (arccos, 'Real.arccos'),
    ],
)
def test_new_real_functions_render(function: Callable[[object], object], lean: str) -> None:
    """Render the hyperbolic and inverse trigonometric functions through the core table."""
    assert str(symbolic(function(xr), TYPED, lean_type='')) == f'{lean} x'


def test_real_powers_and_logarithms_to_a_base() -> None:
    """Render a real power and Sage's form of a logarithm to a base."""
    assert str(symbolic(xr ** (SR(3) / 2), TYPED, lean_type='')) == 'x ^ (3 / 2 : ℝ)'
    assert str(symbolic(log(xr) / log(SR(2)), TYPED, lean_type='')) == '(Real.log x) / (Real.log 2)'


def test_integer_operators_render_at_their_type_and_cast() -> None:
    """Render integer-valued operators at ℕ (or ℤ) and cast them into the carrier."""
    assert str(symbolic(factorial(nn) + xr, TYPED)) == '(x + ((Nat.factorial n : ℕ) : ℝ) : ℝ)'
    assert str(symbolic(floor(xr), TYPED)) == '((Int.floor x : ℤ) : ℝ)'
    assert str(symbolic(ceil(xr), TYPED, lean_type='ℤ')) == '(Int.ceil x : ℤ)'
    assert str(symbolic(TYPED.goal.expr + xr, TYPED)) == '(x + ((n % 7 : ℕ) : ℝ) : ℝ)'


def test_rendering_at_a_named_integer_type() -> None:
    """Render at ℕ or ℤ when asked, ascribing the term."""
    assert str(symbolic(nn + 1, TYPED, lean_type='ℕ')) == '(n + 1 : ℕ)'
    assert str(symbolic(kk - 1, TYPED, lean_type='ℤ')) == '(k - 1 : ℤ)'


def test_rendering_refuses_meaningless_integer_text() -> None:
    """Refuse a subtraction at ℕ and a fraction at ℕ or ℤ, pointing to a type where they mean what Sage means."""
    with pytest.raises(CertificateError, match='truncates'):
        symbolic(nn - 1, TYPED, lean_type='ℕ')
    with pytest.raises(CertificateError, match='field type'):
        symbolic(nn / 2, TYPED, lean_type='ℤ')
    assert str(symbolic(nn * (nn - 1) / 2, TYPED, lean_type='ℚ')) == '((n - 1) * n / 2 : ℚ)'


def test_typed_rendering_parses_in_lean(lean_parses: Callable[[list[Lean]], str]) -> None:
    """Every typed rendering parses as Lean."""
    snippets = [
        symbolic(factorial(nn) + xr, TYPED),
        symbolic(floor(xr) + ceil(xr), TYPED),
        symbolic(TYPED.goal.expr + xr, TYPED),
        symbolic(nn + 1, TYPED, lean_type='ℕ'),
        symbolic(arcsin(xr) + cosh(xr) + xr ** (SR(3) / 2), TYPED),
    ]
    assert lean_parses(snippets) == ''


def _log_problem(goal_expr: str, goal_text: str, extensions: list[dict[str, object]] | None = None) -> Problem:
    """Return a problem over `x`, `y` with `hx : x ≠ 0`, `hy : y ≠ 0` and the given goal."""
    return read_problem(
        {
            'vars': ['x0', 'x1'],
            'atoms': ['x', 'y'],
            'carrier': 'ℝ',
            'hyps': [
                {'name': 'hx', 'poly': 'x0', 'rel': 'ne', 'text': 'x ≠ 0'},
                {'name': 'hy', 'poly': 'x1', 'rel': 'ne', 'text': 'y ≠ 0'},
            ],
            'goal': {'kind': 'other', 'rel': 'eq', 'expr': goal_expr, 'text': goal_text},
            'namespaces': ['mathlib', 'project'] if extensions else ['mathlib'],
            'extensions': extensions or [],
        },
    )


def test_rewrite_candidates_bind_side_conditions() -> None:
    """Select `Real.log_mul` by its pattern, fill its side conditions from the bindings, and pass the hypotheses."""
    prob = _log_problem('(log((x0 * x1))) - ((log(x0) + log(x1)))', 'Real.log (x * y) = Real.log x + Real.log y')
    (candidate,) = rewrite_candidates(prob)
    assert candidate.lemma == 'Real.log_mul'
    assert sorted(candidate.side) == ['x ≠ 0', 'y ≠ 0']
    assert str(candidate.emit(prob)) == 'rw [Real.log_mul (by assumption) (by assumption)]'


def test_rewrite_candidates_prefer_the_quotient_lemma() -> None:
    """Select `Real.log_div` for a quotient, ahead of `Real.log_mul`, whose pattern also matches it."""
    prob = _log_problem('(log((x0 / x1))) - ((log(x0) - log(x1)))', 'Real.log (x / y) = Real.log x - Real.log y')
    assert rewrite_candidates(prob)[0].lemma == 'Real.log_div'


def test_rewrite_candidates_need_every_function_and_a_match() -> None:
    """Offer nothing when the goal does not mention the entry's functions or its pattern does not match."""
    assert rewrite_candidates(_log_problem('(log(x0)) - (x1)', 'Real.log x = y')) == []


def test_rewrite_candidates_include_project_entries() -> None:
    """Offer a project rewrite after the core ones, with an unfilled side condition reported on emission."""
    extension = {
        'namespace': 'project',
        'rewrites': [{'lemma': 'Real.arcosh_cosh', 'functions': ['Real.arcosh'], 'side': ['0 ≤ x']}],
    }
    prob = _log_problem('(x0) - (x0)', 'Real.arcosh (Real.cosh x) = x', [extension])
    (candidate,) = rewrite_candidates(prob)
    assert candidate.namespace == 'project'
    with pytest.raises(CertificateError, match='0 ≤ x'):
        candidate.emit(prob)
    assert str(candidate.emit(prob, proofs={'0 ≤ x': 'positivity'})) == 'rw [Real.arcosh_cosh (by positivity)]'
