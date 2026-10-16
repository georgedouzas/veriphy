"""Linear algebra over explicit vectors and matrices: Sage computes the data, Lean checks the packaged statement.

Sage computes echelon forms, non-singular minors, rank factorisations, kernel bases with their free coordinates,
dependence relations, congruences `Pᵀ S P = D` of symmetric matrices, and points where a map fails to be linear. The
emitters state each claim through the lemmas of `Veriphy/Kit/Linear.lean` and close the resulting finite checks by
evaluation (`simp +decide` on determinants, `ext` and `fin_cases` on vector identities).
"""

import itertools
from collections.abc import Callable, Sequence

from sage.all import QQ, SR, identity_matrix, lcm, matrix
from sage.matrix.matrix0 import Matrix
from sage.structure.element import RingElement

from veriphy.core import CertificateError


def nonzero_minor(m: Matrix, size: int) -> tuple[list[int], list[int]]:
    """Return rows and columns of a non-singular `size × size` minor.

    Args:
        m: The matrix.
        size: The minor's size.

    Returns:
        The row and column indices, increasing.

    Raises:
        CertificateError: If every minor of that size is singular (the rank is smaller).

    Examples:
        >>> nonzero_minor(matrix(QQ, [[1, 2, 3], [2, 4, 6]]), 1)
        ([0], [0])
        >>> nonzero_minor(matrix(QQ, [[1, 2, 0], [0, 1, 1]]), 2)
        ([0, 1], [0, 1])
    """
    pivots_rows = list(m.transpose().pivots())
    pivots_cols = list(m.pivots())
    if len(pivots_cols) >= size:
        rows = pivots_rows[:size]
        for cols in itertools.combinations(range(m.ncols()), size):
            if m.matrix_from_rows_and_columns(rows, list(cols)).det() != 0:
                return rows, list(cols)
    message = f'every {size} × {size} minor is singular: the rank is {m.rank()}'
    raise CertificateError(message)


def rank_factorization(m: Matrix) -> tuple[Matrix, Matrix]:
    """Return `B` and `C` with `m = B * C` and inner size the rank: the pivot columns and the reduced echelon rows.

    Args:
        m: The matrix.

    Returns:
        `B` (`rows × rank`) and `C` (`rank × columns`).

    Examples:
        >>> b, c = rank_factorization(matrix(QQ, [[1, 2, 3], [2, 4, 6]]))
        >>> b.list(), c.list()
        ([1, 2], [1, 2, 3])
    """
    pivots = list(m.pivots())
    b = m.matrix_from_columns(pivots)
    c = m.rref().matrix_from_rows(range(len(pivots)))
    if b * c != m:  # an invariant of the reduced echelon form
        message = 'the rank factorisation failed to reproduce the matrix'
        raise CertificateError(message)
    return b, c


def dependence_relation(vectors: Sequence[Sequence[object]]) -> list[object]:
    """Return a non-trivial relation `Σ cᵢ vᵢ = 0` among the vectors, with integer coefficients when possible.

    Args:
        vectors: The family.

    Returns:
        The coefficients.

    Raises:
        CertificateError: If the family is linearly independent.

    Examples:
        >>> dependence_relation([[1, 2], [2, 4]])
        [2, -1]
    """
    m = matrix(QQ, vectors)
    kernel = m.left_kernel().basis()
    if not kernel:
        message = 'the family is linearly independent: no relation exists'
        raise CertificateError(message)
    relation = kernel[0]
    scale = lcm_denominator(list(relation))
    return [c * scale for c in relation]


def lcm_denominator(values: Sequence[object]) -> object:
    """Return the least common multiple of the denominators of rational values.

    Args:
        values: The rationals.

    Returns:
        The multiple.
    """
    return lcm([QQ(v).denominator() for v in values])


def kernel_basis(m: Matrix) -> tuple[list[list[object]], list[int]]:
    """Return a kernel basis of `m` from its reduced echelon form, and the free columns that coordinate it.

    The basis vector for free column `j` has a `1` at `j` and `0` at the other free columns, so a kernel vector `x`
    is `Σⱼ x j • vⱼ`.

    Args:
        m: The matrix.

    Returns:
        The basis vectors and the free columns.

    Examples:
        >>> kernel_basis(matrix(QQ, [[1, 1, 1]]))
        ([[-1, 1, 0], [-1, 0, 1]], [1, 2])
    """
    r = m.rref()
    pivots = list(r.pivots())
    free = [j for j in range(m.ncols()) if j not in pivots]
    basis = []
    for j in free:
        v = [QQ(0)] * m.ncols()
        v[j] = QQ(1)
        for row, p in enumerate(pivots):
            v[p] = -r[row, j]
        basis.append(v)
    return basis, free


def coordinates(target: Sequence[object], basis: Sequence[Sequence[object]]) -> list[object]:
    """Return the coordinates of a vector in a family spanning it.

    Args:
        target: The vector.
        basis: The family.

    Returns:
        Coefficients `c` with `Σ cᵢ bᵢ = target`.

    Raises:
        CertificateError: If the vector is not in the span.

    Examples:
        >>> coordinates([1, 3], [[1, 1], [0, 1]])
        [1, 2]
    """
    m = matrix(QQ, basis)
    try:
        return list(m.solve_left(matrix(QQ, [list(target)]))[0])
    except ValueError:
        message = f'{list(target)} is not in the span of the family'
        raise CertificateError(message) from None


def symmetric_congruence(s: Matrix) -> tuple[Matrix, list[object]]:
    """Return `P` invertible and the diagonal `d` with `Pᵀ S P = diag(d)`, by symmetric Gaussian elimination.

    A zero pivot with a non-zero entry in its row is first made non-zero by adding a later basis vector (or the
    sum of two), as in the reduction of a quadratic form to squares.

    Args:
        s: A symmetric matrix over ℚ.

    Returns:
        `P` and `d`.

    Raises:
        CertificateError: If the matrix is not symmetric.

    Examples:
        >>> p, d = symmetric_congruence(matrix(QQ, [[2, 1, 0], [1, 2, 1], [0, 1, 2]]))
        >>> d
        [2, 3/2, 4/3]
        >>> p, d = symmetric_congruence(matrix(QQ, [[0, 1], [1, 0]]))
        >>> d, p.transpose() * matrix(QQ, [[0, 1], [1, 0]]) * p == matrix.diagonal(d)
        ([2, -1/2], True)
    """
    if s != s.transpose():
        message = 'the matrix is not symmetric'
        raise CertificateError(message)
    n = s.nrows()
    a = matrix(QQ, s)
    p = identity_matrix(QQ, n)
    for k in range(n):
        if a[k, k] == 0:
            partner = next((j for j in range(k + 1, n) if a[k, j] != 0), None)
            if partner is None:
                continue
            step = identity_matrix(QQ, n)
            step[partner, k] = 1 if a[partner, partner] == 0 or a[k, partner] != -a[partner, partner] / 2 else -1
            a = step.transpose() * a * step
            p = p * step
        for j in range(k + 1, n):
            if a[k, j] != 0:
                step = identity_matrix(QQ, n)
                step[k, j] = -a[k, j] / a[k, k]
                a = step.transpose() * a * step
                p = p * step
    return p, [a[i, i] for i in range(n)]


def signature(d: Sequence[RingElement]) -> tuple[int, int, int]:
    """Return the numbers of positive, negative and zero entries of a diagonal.

    Args:
        d: The diagonal.

    Returns:
        The counts.

    Examples:
        >>> signature([2, -1, 0, 3])
        (2, 1, 1)
    """
    return (sum(1 for x in d if x > 0), sum(1 for x in d if x < 0), sum(1 for x in d if x == 0))


def nonlinearity_witness(g: Callable[[RingElement], RingElement]) -> tuple[str, list[object]]:
    """Return how a map of one real variable fails to be linear: `map_zero`, `map_add` or `map_smul`, and its points.

    Args:
        g: The map, a Python function on Sage values.

    Returns:
        The failing law and its arguments.

    Raises:
        CertificateError: If the map passes the three laws at every small rational test point.

    Examples:
        >>> nonlinearity_witness(lambda x: x ** 2)
        ('map_smul', [2, 1])
        >>> nonlinearity_witness(lambda x: x + 1)
        ('map_zero', [])
    """
    if SR(g(QQ(0))) != 0:
        return 'map_zero', []
    points = [QQ(v) for v in (1, 2, -1, QQ(1) / 2, 3)]
    for c, x in itertools.product(points, repeat=2):
        if SR(g(c * x) - c * g(x)).simplify_full() != 0:
            return 'map_smul', [c, x]
    for x, y in itertools.product(points, repeat=2):
        if SR(g(x + y) - g(x) - g(y)).simplify_full() != 0:
            return 'map_add', [x, y]
    message = 'the map passes additivity and homogeneity at every test point; it may be linear'
    raise CertificateError(message)
