"""Find certificates: factorizations, sums of squares, roots, ideal cofactors, closed sums, Farkas and witnesses."""

import itertools
from collections.abc import Sequence

import sage.all as sage_all
from sage.all import QQ, matrix, vector
from sage.matrix.matrix0 import Matrix
from sage.modules.free_module_element import FreeModuleElement
from sage.rings.polynomial.multi_polynomial import MPolynomial
from sage.rings.polynomial.multi_polynomial_ring_base import MPolynomialRing_base
from sage.rings.polynomial.polynomial_element import Polynomial
from sage.rings.rational import Rational

from veriphy.core import CertificateError, Method, ParamError
from veriphy.oracle._lp import solve_exact_lp
from veriphy.oracle._registry import (
    _coerce_poly,
    _coerce_poly_list,
    _coerce_relations,
    _coerce_ring,
    _coerce_str,
    _coerce_univariate_ring,
    _register_method,
)

CERTIFICATE_METHODS: dict[str, Method] = {}
QUADRATIC = 2
PERTURBATION_SCALES = (1, 2, 3, 5, 7, 11)
PERTURBED_DIRECTIONS = 6

SquareList = list[tuple[Rational, MPolynomial]]


@_register_method(CERTIFICATE_METHODS, 'factor', vars=_coerce_ring, poly=_coerce_poly)
def _find_factorization(R: MPolynomialRing_base, poly: MPolynomial) -> dict[str, object]:
    """Return the factorization of a polynomial over QQ as a unit and factors with multiplicities."""
    fac = poly.factor()
    return {'unit': QQ(fac.unit()), 'factors': [{'terms': q, 'mult': int(m)} for q, m in fac]}


def _multiply_sos(left: SquareList, right: SquareList) -> SquareList:
    """Return the product of two weighted sums of squares as one weighted sum of squares."""
    return [(c * d, q * r) for (c, q) in left for (d, r) in right]


def _complete_square(f: MPolynomial, R: MPolynomialRing_base) -> SquareList | None:
    """Return a positive-definite single-variable quadratic as a completed square, or `None`."""
    if len(f.variables()) != 1 or f.degree() != QUADRATIC:
        return None
    fu = f.univariate_polynomial()
    a, b, c = QQ(fu[2]), QQ(fu[1]), QQ(fu[0])
    if a <= 0 or b**2 - 4 * a * c >= 0:
        return None
    x = R(f.variables()[0])
    return [(a, x + b / (2 * a)), (c - b**2 / (4 * a), R.one())]


def _sos_of_irreducible(f: MPolynomial, R: MPolynomialRing_base) -> SquareList:
    """Return one irreducible factor of odd multiplicity as a weighted sum of squares."""
    if f.degree() == 0:
        c = QQ(f)
        if c < 0:
            message = f'negative constant factor {c}'
            raise CertificateError(message)
        return [(c, R.one())]
    completed = _complete_square(f, R)
    if completed is None:
        message = (
            f'factor {f} with odd multiplicity is not a supported SOS building block '
            '(supported: constants, single-variable positive-definite quadratics)'
        )
        raise CertificateError(message)
    return completed


def _sos_from_hints(p: MPolynomial, hints: Sequence[MPolynomial], R: MPolynomialRing_base) -> SquareList:
    """Return exact weights `c_0, c_i >= 0` with `p = c_0 + sum c_i h_i^2` for the caller's hinted squares."""
    squares = [R.one()] + [h**2 for h in hints]
    monomials = sorted(set().union(*[set(q.monomials()) for q in squares]) | set(p.monomials()))
    rows = [([q.monomial_coefficient(m) for q in squares], -p.monomial_coefficient(m)) for m in monomials]
    weights = solve_exact_lp(len(squares), eqs=rows, objective=[1] * len(squares), nonneg=True)
    if weights is None:
        message = 'no nonnegative combination of the hinted squares equals the polynomial'
        raise CertificateError(message)
    if sum(v * q for v, q in zip(weights, squares, strict=True)) != p:
        message = 'hinted SOS fit is not exact'
        raise CertificateError(message)
    return [(v, R.one() if i == 0 else hints[i - 1]) for i, v in enumerate(weights) if v != 0]


def _sos_from_factors(p: MPolynomial, R: MPolynomialRing_base) -> SquareList:
    """Return a weighted sum of squares built from the factorization of `p`."""
    fac = p.factor()
    unit = QQ(fac.unit())
    if unit < 0:
        message = f'negative leading unit {unit}: polynomial is not SOS'
        raise CertificateError(message)
    sos: SquareList = [(unit, R.one())]
    for f, m in fac:
        half, odd = divmod(m, 2)
        if half:
            sos = _multiply_sos(sos, [(QQ(1), f**half)])
        if odd:
            sos = _multiply_sos(sos, _sos_of_irreducible(f, R))
    return sos


@_register_method(CERTIFICATE_METHODS, 'sos', vars=_coerce_ring, poly=_coerce_poly, hints=_coerce_poly_list)
def _find_sos(R: MPolynomialRing_base, poly: MPolynomial, hints: list[MPolynomial]) -> dict[str, object]:
    """Return an exact decomposition `poly = sum c_i * q_i^2` certifying `0 <= poly`."""
    if poly == 0:
        return {'squares': []}
    sos = _sos_from_hints(poly, hints, R) if hints else _sos_from_factors(poly, R)
    return {'squares': [{'coeff': c, 'terms': q} for c, q in sos]}


@_register_method(CERTIFICATE_METHODS, 'roots', var=_coerce_univariate_ring, poly=_coerce_poly)
def _find_roots(R: object, poly: Polynomial) -> dict[str, object]:
    """Return the rational roots of a univariate polynomial over QQ."""
    return {'roots': [QQ(r) for r, _ in poly.roots(QQ)]}


@_register_method(CERTIFICATE_METHODS, 'lincomb', vars=_coerce_ring, target=_coerce_poly, hyps=_coerce_poly_list)
def _find_cofactors(R: MPolynomialRing_base, target: MPolynomial, hyps: list[MPolynomial]) -> dict[str, object]:
    """Return cofactors `c_i` with `target = sum c_i * hyp_i`, an ideal-membership certificate."""
    if not hyps:
        raise ParamError(param='hyps', reason='no hypotheses to combine')
    return {'cofactors': list(target.lift(R.ideal(hyps)))}


@_register_method(CERTIFICATE_METHODS, 'sum', summand=_coerce_str)
def _find_closed_sum(summand: str) -> dict[str, object]:
    """Return the closed form of `sum(f(k), k, 0, n-1)` as a polynomial in `n` over QQ."""
    k, n = sage_all.var('k'), sage_all.var('n')
    try:
        f = sage_all.SR(summand)
    except (TypeError, ValueError, SyntaxError) as exc:
        raise ParamError(param='summand', reason=str(exc)) from exc
    if set(f.variables()) - {k}:
        raise ParamError(param='summand', reason='may only contain the variable k')
    closed = f.sum(k, 0, n - 1)
    return {'closed_form': closed.expand().polynomial(QQ), 'var': 'n'}


def _farkas_rows(
    R: MPolynomialRing_base,
    ps: list[MPolynomial],
) -> tuple[list[tuple[list[Rational], int]], list[Rational]]:
    """Return the equality rows that cancel every variable, and the constant terms (kappa coefficients)."""
    nonlinear = {i for i, q in enumerate(ps) if q.degree() > 1}
    n = len(ps)
    rows: list[tuple[list[Rational], int]] = [([QQ(int(j == i)) for j in range(n)], 0) for i in nonlinear]
    for x in R.gens():
        rows.append(([QQ(0) if i in nonlinear else QQ(q.monomial_coefficient(x)) for i, q in enumerate(ps)], 0))
    kappa = [QQ(0) if i in nonlinear else QQ(q.constant_coefficient()) for i, q in enumerate(ps)]
    return rows, kappa


@_register_method(
    CERTIFICATE_METHODS,
    'farkas',
    vars=_coerce_ring,
    polys=_coerce_poly_list,
    rels=_coerce_relations('eq', 'le', 'lt'),
)
def _find_farkas(R: MPolynomialRing_base, polys: list[MPolynomial], rels: list[str]) -> dict[str, object]:
    """Return Farkas multipliers that make `sum m_i p_i` a contradictory constant, by exact rational LPs."""
    if len(rels) != len(polys):
        raise ParamError(param='rels', reason=f'expected {len(polys)} relations, got {len(rels)}')
    n = len(polys)
    rows, kappa = _farkas_rows(R, polys)
    nonneg = [i for i, r in enumerate(rels) if r != 'eq']
    weight = [0 if r == 'eq' else 1 for r in rels]
    strict = [1 if r == 'lt' else 0 for r in rels]
    attempts = [(rows, [([-c for c in kappa], 1)])]
    if any(strict):
        attempts.append(([*rows, (kappa, 0)], [([-s for s in strict], 1)]))
    for eqs, les in attempts:
        sol = solve_exact_lp(n, eqs=eqs, les=les, objective=weight, nonneg=nonneg)
        if sol is not None:
            constant = sum(c * q.constant_coefficient() for c, q in zip(sol, polys, strict=True))
            uses_strict = any(c != 0 and r == 'lt' for c, r in zip(sol, rels, strict=True))
            return {'multipliers': sol, 'kappa': QQ(constant), 'strict': bool(uses_strict)}
    message = 'the linear hypotheses are consistent (no Farkas certificate)'
    raise CertificateError(message)


class _System:
    """Hold the constraint system of an `exists` request.

    Args:
        R: The polynomial ring.
        eqs: Polynomials `p` with `p = 0`.
        les: Polynomials `p` with `p <= 0`.
        lts: Polynomials `p` with `p < 0`.
        nes: Polynomials `p` with `p != 0`.
    """

    def __init__(
        self,
        R: MPolynomialRing_base,
        eqs: list[MPolynomial],
        les: list[MPolynomial],
        lts: list[MPolynomial],
        nes: list[MPolynomial],
    ) -> None:
        self.R = R
        self.eqs = eqs
        self.les = les
        self.lts = lts
        self.nes = nes

    def holds_at(self, point: Sequence[Rational]) -> bool:
        """Return whether every constraint holds at `point`."""
        sub = dict(zip(self.R.gens(), point, strict=True))
        return (
            all(q.subs(sub) == 0 for q in self.eqs)
            and all(q.subs(sub) <= 0 for q in self.les)
            and all(q.subs(sub) < 0 for q in self.lts)
            and all(q.subs(sub) != 0 for q in self.nes)
        )

    def is_linear(self) -> bool:
        """Return whether every equation and inequality has degree at most one."""
        return all(q.degree() <= 1 for q in self.eqs + self.les + self.lts)


def _affine_solutions(system: _System) -> tuple[FreeModuleElement, Matrix]:
    """Return a particular solution `x0` and kernel basis `K` of the linear equations, so solutions are `x0 + t K`."""
    gens = system.R.gens()
    n = len(gens)
    if not system.eqs:
        return vector(QQ, [0] * n), matrix.identity(QQ, n)
    a = matrix(QQ, [[QQ(q.monomial_coefficient(x)) for x in gens] for q in system.eqs])
    b = vector(QQ, [-QQ(q.constant_coefficient()) for q in system.eqs])
    try:
        x0 = a.solve_right(b)
    except ValueError as exc:
        message = 'the equations are inconsistent'
        raise CertificateError(message) from exc
    return x0, a.right_kernel().basis_matrix()


def _in_parameters(
    q: MPolynomial,
    x0: FreeModuleElement,
    kernel: Matrix,
    gens: Sequence[MPolynomial],
) -> tuple[list[Rational], Rational]:
    """Return `q(x0 + t K)` as coefficients in `t` and a constant."""
    const = QQ(q.constant_coefficient()) + sum(QQ(q.monomial_coefficient(x)) * x0[j] for j, x in enumerate(gens))
    coeffs = [
        sum(QQ(q.monomial_coefficient(x)) * kernel[r, j] for j, x in enumerate(gens)) for r in range(kernel.nrows())
    ]
    return coeffs, const


def _feasible_parameters(system: _System, x0: FreeModuleElement, kernel: Matrix) -> list[Rational]:
    """Return parameters `t` meeting the inequalities, strict ones with the largest margin up to one."""
    k = kernel.nrows()
    if not (system.les or system.lts):
        return [QQ(0)] * k
    gens = system.R.gens()
    rows = [([*coeffs, 0], const) for coeffs, const in (_in_parameters(q, x0, kernel, gens) for q in system.les)]
    rows += [([*coeffs, 1], const) for coeffs, const in (_in_parameters(q, x0, kernel, gens) for q in system.lts)]
    rows.append(([0] * k + [1], -1))
    sol = solve_exact_lp(k + 1, les=rows, objective=[0] * k + [1], nonneg=[k], maximize=True)
    if sol is None:
        message = 'the linear inequalities are infeasible'
        raise CertificateError(message)
    return sol[:k]


def _linear_witness(system: _System) -> list[Rational]:
    """Return a rational point of a linear system, perturbed off any disequalities."""
    x0, kernel = _affine_solutions(system)
    base = _feasible_parameters(system, x0, kernel)
    k, n = kernel.nrows(), len(system.R.gens())
    span = min(k, PERTURBED_DIRECTIONS)
    candidates = [base]
    for scale in PERTURBATION_SCALES:
        for d in itertools.product(range(-1, 2), repeat=span):
            step = list(d) + [0] * (k - span)
            candidates.append([base[r] + QQ(step[r]) / scale for r in range(k)])
    for c in candidates:
        point = [x0[j] + sum(kernel[r, j] * c[r] for r in range(k)) for j in range(n)]
        if system.holds_at(point):
            return [QQ(v) for v in point]
    message = 'no rational witness found'
    raise CertificateError(message)


def _nonlinear_witness(system: _System) -> list[Rational]:
    """Return a rational point among the solutions Sage's solver finds for the equations."""
    sv = [sage_all.SR.var(str(g)) for g in system.R.gens()]
    for sol in sage_all.solve([sage_all.SR(str(q)) == 0 for q in system.eqs], sv, solution_dict=True):
        try:
            point = [QQ(sol[v]) for v in sv]
        except (TypeError, ValueError, KeyError):
            continue
        if system.holds_at(point):
            return point
    message = 'no rational witness found'
    raise CertificateError(message)


@_register_method(
    CERTIFICATE_METHODS,
    'exists',
    vars=_coerce_ring,
    eqs=_coerce_poly_list,
    les=_coerce_poly_list,
    lts=_coerce_poly_list,
    nes=_coerce_poly_list,
)
def _find_witness(
    R: MPolynomialRing_base,
    eqs: list[MPolynomial],
    les: list[MPolynomial],
    lts: list[MPolynomial],
    nes: list[MPolynomial],
) -> dict[str, object]:
    """Return a rational point satisfying equations, linear inequalities and disequalities."""
    system = _System(R, eqs, les, lts, nes)
    point = _linear_witness(system) if system.is_linear() else _nonlinear_witness(system)
    return {'point': point}
