"""Test the certificate methods on the inputs the Lean tactic suite sends."""

from collections.abc import Callable

from sage.all import QQ

from veriphy.core import JsonObject

Ok = Callable[..., JsonObject]
Err = Callable[..., str]


def test_answer_request_factor(ok: Ok) -> None:
    """Return the unit and the factors with multiplicities."""
    result = ok('factor', poly='(3 * x0^2 * x1) - (3 * x1^3)', vars=['x0', 'x1'])
    assert result['unit'] == '3'
    factors = result['factors']
    assert isinstance(factors, list)
    assert len(factors) == 3
    assert all(isinstance(f, dict) and set(f) == {'mult', 'terms'} for f in factors)


def test_answer_request_sos_from_factors(ok: Ok) -> None:
    """Return squares with coefficients for a polynomial that factors into squares."""
    squares = ok('sos', poly='x0^4 - 2*x0^3 + 2*x0^2 - 2*x0 + 1', vars=['x0'])['squares']
    assert isinstance(squares, list)
    assert squares
    assert isinstance(squares[0], dict)
    assert set(squares[0]) == {'coeff', 'terms'}


def test_answer_request_sos_single_variable_quadratic(ok: Ok) -> None:
    """Complete the square of a positive-definite quadratic."""
    squares = ok('sos', poly='x0^2 + x0 + 1', vars=['x0'])['squares']
    assert isinstance(squares, list)
    assert len(squares) == 2


def test_answer_request_sos_hints(ok: Ok, err: Err) -> None:
    """Weight the hinted squares exactly, and report when no weights exist."""
    result = ok(
        'sos',
        poly='x0^4 + 2*x0^2*x1^2 + x1^4 - 2*x0^2 - 2*x1^2 + 1 + (x0 - x1)^2',
        vars=['x0', 'x1'],
        hints=['x0^2 + x1^2 - 1', 'x0 - x1'],
    )
    assert isinstance(result['squares'], list)
    assert len(result['squares']) == 2
    assert 'no nonnegative combination' in err('sos', poly='-1', vars=['x0'], hints=['x0'])


def test_answer_request_roots(ok: Ok) -> None:
    """Return every rational root."""
    roots = ok('roots', poly='2*x0^3 - 3*x0^2 - 3*x0 + 2', var='x0')['roots']
    assert isinstance(roots, list)
    assert sorted(map(str, roots)) == sorted(['-1', '1/2', '2'])


def test_answer_request_lincomb(ok: Ok, err: Err) -> None:
    """Return one cofactor per hypothesis, and name `hyps` when there are none."""
    result = ok(
        'lincomb',
        target='(x0^2 + x1^2) - (5)',
        hyps=['(x0 + x1) - (3)', '(x0*x1) - (2)'],
        vars=['x0', 'x1'],
    )
    assert isinstance(result['cofactors'], list)
    assert len(result['cofactors']) == 2
    assert "'hyps'" in err('lincomb', target='x0', hyps=[], vars=['x0'])


def test_answer_request_sum(ok: Ok) -> None:
    """Return the closed form of a power sum as a polynomial in `n`."""
    result = ok('sum', summand='k^2')
    assert result['var'] == 'n'
    closed = result['closed_form']
    assert isinstance(closed, list)
    assert {t['coeff'] for t in closed if isinstance(t, dict)} == {'1/3', '-1/2', '1/6'}


def test_answer_request_farkas(ok: Ok) -> None:
    """Return multipliers with a positive constant for an inconsistent system."""
    result = ok(
        'farkas',
        polys=['(x0 + x1) - (1)', '(x0 - x1) - (3)', '(0) - (x1)'],
        rels=['le', 'eq', 'le'],
        vars=['x0', 'x1'],
    )
    assert set(result) == {'multipliers', 'kappa', 'strict'}
    assert QQ(str(result['kappa'])) > 0


def test_answer_request_farkas_strict(ok: Ok) -> None:
    """Use a strict hypothesis with a zero constant."""
    result = ok('farkas', polys=['x0 - x1', 'x1 - x0'], rels=['lt', 'le'], vars=['x0', 'x1'])
    assert result['strict'] is True
    assert result['kappa'] == '0'


def test_answer_request_farkas_consistent(err: Err) -> None:
    """Report a consistent system as having no certificate."""
    error = err('farkas', polys=['x0 - 1'], rels=['le'], vars=['x0'])
    assert error.startswith('farkas: ')
    assert 'no Farkas certificate' in error


def test_answer_request_farkas_only_equalities(ok: Ok, err: Err) -> None:
    """Handle systems with equalities only, which give the LP no inequality rows."""
    assert 'no Farkas certificate' in err(
        'farkas',
        polys=['x0 - x1', 'x1 - x2'],
        rels=['eq', 'eq'],
        vars=['x0', 'x1', 'x2'],
    )
    result = ok('farkas', polys=['x0 - 1', 'x0 - 2'], rels=['eq', 'eq'], vars=['x0'])
    assert QQ(str(result['kappa'])) > 0


def test_answer_request_exists(ok: Ok) -> None:
    """Return witnesses for an eigenvector system and for strict inequalities."""
    point = ok('exists', vars=['x0', 'x1'], eqs=['2*x0 + x1 - 3*x0', 'x0 + 2*x1 - 3*x1'], nes=['x0'])['point']
    assert isinstance(point, list)
    assert len(point) == 2
    point = ok('exists', vars=['x0', 'x1'], eqs=['x0 + x1 - 1'], lts=['0 - x0', 'x0 - x1'])['point']
    assert isinstance(point, list)
    x, y = (QQ(str(v)) for v in point)
    assert x + y == 1
    assert 0 < x < y


def test_answer_request_exists_without_inequalities(ok: Ok) -> None:
    """Return a witness when there are no inequalities, so no LP is built."""
    point = ok('exists', vars=['x0', 'x1'], eqs=['x0 - x1'])['point']
    assert isinstance(point, list)
    assert point[0] == point[1]
