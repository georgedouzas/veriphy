"""Find exact sums of squares from a numeric semidefinite program."""

import itertools
from collections.abc import Sequence

from cvxopt import matrix as cvx_matrix
from cvxopt import solvers
from sage.all import QQ, matrix, vector
from sage.matrix.matrix0 import Matrix
from sage.rings.polynomial.multi_polynomial import MPolynomial
from sage.rings.rational import Rational

from veriphy.core import CertificateError

DENOMINATORS = (10**4, 10**6, 10**8, 10**10)
MARGIN_TOLERANCE = -1e-9


def _half_basis(p: MPolynomial) -> list[MPolynomial]:
    """Return the monomials whose squares can appear in `p`: each exponent at most half of `p`'s largest one."""
    ring = p.parent()
    bounds = [max((e[i] for e in p.exponents()), default=0) // 2 for i in range(ring.ngens())]
    half_degree = p.total_degree() // 2
    exponents = [e for e in itertools.product(*(range(b + 1) for b in bounds)) if sum(e) <= half_degree]
    return [ring.monomial(*e) for e in exponents]


def _gram_space(p: MPolynomial, basis: list[MPolynomial]) -> tuple[Matrix, list[Matrix]]:
    """Return a symmetric `Q₀` and a basis `Nⱼ` of symmetric matrices with `zᵀ(Q₀ + Σ yⱼNⱼ)z = p` for every `y`."""
    m = len(basis)
    pairs = [(i, j) for i in range(m) for j in range(i, m)]
    products = sorted({basis[i] * basis[j] for i, j in pairs} | set(p.monomials()))
    rows = [[QQ(2 - (i == j)) if basis[i] * basis[j] == mono else QQ(0) for i, j in pairs] for mono in products]
    target = vector(QQ, [QQ(p.monomial_coefficient(mono)) for mono in products])
    system = matrix(QQ, rows)
    try:
        particular = system.solve_right(target)
    except ValueError as exc:
        message = 'no Gram matrix matches the polynomial (it is not a sum of squares of polynomials)'
        raise CertificateError(message) from exc

    def symmetric(values: Sequence[Rational]) -> Matrix:
        """Return the symmetric matrix with the given upper-triangular entries."""
        q = matrix(QQ, m, m)
        for (i, j), value in zip(pairs, values, strict=True):
            q[i, j] = q[j, i] = value
        return q

    return symmetric(particular), [symmetric(row) for row in system.right_kernel().basis()]


def _maximize_margin(q0: Matrix, directions: list[Matrix]) -> tuple[list[float], float]:
    """Return weights `y` and the margin `t` maximizing `t` subject to `Q₀ + Σ yⱼNⱼ - tI ⪰ 0` and `t ≤ 1`."""
    m = q0.nrows()
    identity = matrix.identity(QQ, m)
    columns = [[-float(v) for v in n.list()] for n in directions] + [[float(v) for v in identity.list()]]
    objective = cvx_matrix([0.0] * len(directions) + [-1.0])
    lmi = cvx_matrix(columns)
    lmi_rhs = cvx_matrix([[float(q0[i, j]) for i in range(m)] for j in range(m)])
    bound = cvx_matrix([[0.0] * len(directions) + [1.0]]).T
    solvers.options['show_progress'] = False
    solution = solvers.sdp(objective, Gl=bound, hl=cvx_matrix([1.0]), Gs=[lmi], hs=[lmi_rhs])
    if solution['x'] is None:
        message = 'the semidefinite program found no Gram matrix (the polynomial is not a sum of squares)'
        raise CertificateError(message)
    values = list(solution['x'])
    return values[:-1], values[-1]


def _round(value: float, denominator: int) -> Rational:
    """Return `value` rounded to a rational with the given denominator."""
    return QQ(round(value * denominator)) / denominator


def _squares(q: Matrix, basis: list[MPolynomial]) -> list[tuple[Rational, MPolynomial]]:
    """Return the weighted squares `cᵢ qᵢ²` of an exact positive semidefinite Gram matrix."""
    permutation, lower, diagonal = q.block_ldlt()
    if any(diagonal[i, j] != 0 for i in range(q.nrows()) for j in range(q.nrows()) if i != j):
        message = 'the Gram matrix has a 2x2 pivot block (it is not positive semidefinite)'
        raise CertificateError(message)
    combos = (lower.transpose() * permutation.transpose()) * vector(basis)
    return [(QQ(diagonal[i, i]), combos[i]) for i in range(q.nrows()) if diagonal[i, i] != 0]


def sos_decomposition(p: MPolynomial) -> list[tuple[Rational, MPolynomial]]:
    """Find an exact sum of squares `p = Σ cᵢ qᵢ²` with rational `cᵢ > 0`, through a numeric SDP.

    The Gram matrix is parametrized exactly over QQ. The SDP maximizes its smallest eigenvalue margin, and the
    weights are rounded to rationals at increasing precision until the exact matrix is positive semidefinite. The
    squares come from its exact LDLᵀ factorization and are checked to sum to `p`. A polynomial with real zeros whose
    Gram matrices all lie on the boundary of the positive semidefinite cone with an irrational kernel cannot be
    rounded exactly, and is reported as a failure. Supply candidate squares to the exact LP instead.

    Args:
        p: A polynomial over QQ.

    Returns:
        The `(cᵢ, qᵢ)` pairs.

    Raises:
        CertificateError: If no exact sum of squares is found.

    Examples:
        >>> from veriphy.toolkit import create_ring
        >>> x, y = create_ring(['x', 'y']).gens()
        >>> p = x**4 + 2*x**2*y**2 + y**4 - x**2 - 2*x*y - y**2 + QQ(11) / 10
        >>> sum(c * q**2 for c, q in sos_decomposition(p)) == p
        True
    """
    if p == 0:
        return []
    basis = _half_basis(p)
    q0, directions = _gram_space(p, basis)
    weights, margin = _maximize_margin(q0, directions)
    if margin < MARGIN_TOLERANCE and directions:
        message = f'the polynomial is not a sum of squares (best Gram margin {margin:.3g} < 0)'
        raise CertificateError(message)
    for denominator in DENOMINATORS:
        q = q0 + sum((_round(w, denominator) * n for w, n in zip(weights, directions, strict=True)), q0.parent()(0))
        if q.is_positive_semidefinite():
            squares = _squares(q, basis)
            if sum(c * s**2 for c, s in squares) == p:
                return squares
    message = 'rounding the SDP solution did not give an exact positive semidefinite Gram matrix'
    raise CertificateError(message)
