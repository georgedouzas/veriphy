"""Linear algebra over explicit vectors and matrices: Sage computes the data, Lean checks the packaged statement.

Sage computes echelon forms, non-singular minors, rank factorisations, kernel bases with their free coordinates,
dependence relations, congruences `Pᵀ S P = D` of symmetric matrices, and points where a map fails to be linear. The
emitters state each claim through the lemmas of `Veriphy/Kit/Linear.lean` and close the resulting finite checks by
evaluation (`simp +decide` on determinants, `ext` and `fin_cases` on vector identities).
"""

import functools
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


def span_coordinates(target: Sequence[object], basis: Sequence[Sequence[object]]) -> list[object]:
    """Return the coordinates of a vector in a family spanning it.

    Args:
        target: The vector.
        basis: The family.

    Returns:
        Coefficients `c` with `Σ cᵢ bᵢ = target`.

    Raises:
        CertificateError: If the vector is not in the span.

    Examples:
        >>> span_coordinates([1, 3], [[1, 1], [0, 1]])
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


# the arity of a bilinear map
BILINEAR = 2
DET_NONZERO = (
    'simp +decide [Matrix.det_succ_row_zero, Fin.sum_univ_succ, Fin.succAbove_of_castSucc_lt, '
    'Fin.succAbove_of_le_castSucc, Matrix.diagonal] <;> norm_num'
)
ENTRIES = 'simp [Matrix.mul_apply, Fin.sum_univ_succ, Matrix.transpose_apply, Matrix.diagonal] <;> norm_num'


def _q(x: object) -> str:
    """Return a rational as Lean text."""
    q = QQ(x)
    return str(q) if q.denominator() == 1 else f'({q.numerator()} / {q.denominator()})'


def lean_vector(v: Sequence[object]) -> str:
    """Return a vector literal `![…]`.

    Args:
        v: The entries (rationals).

    Returns:
        The Lean text.

    Examples:
        >>> lean_vector([1, QQ(-1) / 2])
        '![1, (-1 / 2)]'
    """
    return '![' + ', '.join(_q(x) for x in v) + ']'


def lean_family(vectors: Sequence[Sequence[object]], field: str | None = None) -> str:
    """Return a family of vectors as `![![…], …]`, ascribed its type when a field is given.

    Args:
        vectors: The vectors.
        field: The scalars, for an ascription `Fin k → Fin n → K`.

    Returns:
        The Lean text.

    Examples:
        >>> lean_family([[1, 0], [0, 1]], 'ℚ')
        '(![![1, 0], ![0, 1]] : Fin 2 → Fin 2 → ℚ)'
    """
    text = '![' + ', '.join(lean_vector(v) for v in vectors) + ']'
    if field is None or not vectors:
        return text
    return f'({text} : Fin {len(vectors)} → Fin {len(vectors[0])} → {field})'


def lean_matrix(m: Matrix) -> str:
    """Return a matrix literal `!![…; …]`.

    Args:
        m: The matrix.

    Returns:
        The Lean text.

    Examples:
        >>> lean_matrix(matrix(QQ, [[1, 2], [0, 1]]))
        '!![1, 2; 0, 1]'
    """
    return '!![' + '; '.join(', '.join(_q(x) for x in row) for row in m.rows()) + ']'


def _indices(xs: Sequence[int]) -> str:
    """Return indices as a `Fin` vector literal."""
    return '![' + ', '.join(str(i) for i in xs) + ']'


def _membership(target: Sequence[object], basis: Sequence[Sequence[object]], field: str) -> str:
    """Return a proof term of `target ∈ span (range basis)` from its coordinates."""
    c = span_coordinates(target, basis)
    check = 'by ext j <;> fin_cases j <;> simp [Fin.sum_univ_succ, Pi.smul_apply, smul_eq_mul] <;> norm_num'
    return f'(Submodule.mem_span_range_iff_exists_fun {field}).2 ⟨{lean_vector(c)}, {check}⟩'


def _member_of(target: Sequence[object], *, basis: Sequence[Sequence[object]], field: str) -> str:
    """Return a proof term of `target ∈ span (range basis)`, for use as a membership callback."""
    return _membership(target, basis, field)


def _span_le(vectors: Sequence[Sequence[object]], member: Callable[[Sequence[object]], str]) -> str:
    """Return a proof of `span (range vectors) ≤ S` from a proof of membership for each vector."""
    lines = ['rw [Submodule.span_le]', 'rintro _ ⟨i, rfl⟩', 'fin_cases i']
    lines += [f'· exact {member(v)}' for v in vectors]
    return '\n'.join(lines)


def independence_proof(vectors: Sequence[Sequence[object]], *, negated: bool = False) -> str:
    """Return a proof of `LinearIndependent K v` (or `¬ LinearIndependent K v`) for an explicit family.

    Independence comes from a non-singular minor (`Veriphy.Linear.linearIndependent_of_minor`), dependence from an
    explicit relation (`Fintype.not_linearIndependent_iff`).

    Args:
        vectors: The family, as the goal states it.
        negated: Whether the goal is the negation.

    Returns:
        The tactic text.

    Raises:
        CertificateError: If the claim is false.

    Examples:
        >>> print(independence_proof([[1, 2], [2, 4]], negated=True))
        rw [Fintype.not_linearIndependent_iff]
        refine ⟨![2, -1], ?_, 0, by norm_num⟩
        ext j
        fin_cases j <;> simp [Fin.sum_univ_succ, Pi.smul_apply, smul_eq_mul] <;> norm_num
    """
    m = matrix(QQ, vectors)
    independent = m.rank() == m.nrows()
    if negated:
        if independent:
            message = 'the family is linearly independent: its negation is false'
            raise CertificateError(message)
        c = dependence_relation(vectors)
        first = next(i for i, x in enumerate(c) if x != 0)
        return '\n'.join(
            [
                'rw [Fintype.not_linearIndependent_iff]',
                f'refine ⟨{lean_vector(c)}, ?_, {first}, by norm_num⟩',
                'ext j',
                'fin_cases j <;> simp [Fin.sum_univ_succ, Pi.smul_apply, smul_eq_mul] <;> norm_num',
            ],
        )
    if not independent:
        message = f'the family is dependent: {dependence_relation(vectors)} is a relation'
        raise CertificateError(message)
    _, cols = nonzero_minor(m, m.nrows())
    return f'exact Veriphy.Linear.linearIndependent_of_minor _ {_indices(cols)} (by {DET_NONZERO})'


def span_proof(
    vectors: Sequence[Sequence[object]],
    *,
    other: Sequence[Sequence[object]] | None = None,
    kernel_of: Matrix | None = None,
    field: str = 'ℚ',
) -> str:
    """Return a proof of `span (range v) = span (range w)`, or of `span (range v) = ker (A.mulVecLin)`.

    Each inclusion of spans is proved generator by generator with coordinates. For a kernel, the generators are
    shown to lie in it, and a kernel vector `x` is the combination of the generators with coordinates read off
    the rows of a non-singular minor, which `linarith` checks from the kernel equations.

    Args:
        vectors: The left family.
        other: The right family, for a span equality.
        kernel_of: The matrix `A`, for a kernel equality.
        field: The scalars.

    Returns:
        The tactic text.

    Raises:
        CertificateError: If the spans differ, or neither `other` nor `kernel_of` is given.
    """
    lines = ['apply le_antisymm']
    if other is not None:
        for left, right in ((vectors, other), (other, vectors)):
            block = _span_le(left, functools.partial(_member_of, basis=right, field=field))
            lines.append('· ' + block.replace('\n', '\n  '))
        return '\n'.join(lines)
    if kernel_of is None:
        message = 'give the other family (other=…) or the matrix of the kernel (kernel_of=…)'
        raise CertificateError(message)
    a = matrix(QQ, kernel_of)
    v = matrix(QQ, vectors)
    if a * v.transpose() != 0 or v.rank() != a.right_kernel().dimension():
        message = 'the family does not span the kernel'
        raise CertificateError(message)
    rows, _ = nonzero_minor(v.transpose(), v.nrows())
    inverse = v.transpose().matrix_from_rows(rows).inverse()
    coefficients = [
        ' + '.join(f'{_q(inverse[i, k])} * x {rows[k]}' for k in range(len(rows)) if inverse[i, k] != 0) or '0'
        for i in range(v.nrows())
    ]
    inclusion = (
        'rw [Submodule.span_le]\n  rintro _ ⟨i, rfl⟩\n  fin_cases i <;>\n'
        '    (simp only [SetLike.mem_coe, LinearMap.mem_ker, Matrix.mulVecLin_apply]; ext j <;> fin_cases j <;>\n'
        '      simp [Matrix.mulVec, dotProduct, Fin.sum_univ_succ] <;> norm_num)'
    )
    equations = [f'have h{i} := congrFun hx {i}' for i in range(a.nrows())]
    reverse = [
        'intro x hx',
        'rw [LinearMap.mem_ker, Matrix.mulVecLin_apply] at hx',
        *equations,
        f'simp [Matrix.mulVec, dotProduct, Fin.sum_univ_succ] at {" ".join(f"h{i}" for i in range(a.nrows()))}',
        f'refine (Submodule.mem_span_range_iff_exists_fun {field}).2 ⟨![{", ".join(coefficients)}], ?_⟩',
        'ext j <;> fin_cases j <;> simp [Fin.sum_univ_succ, Pi.smul_apply, smul_eq_mul] <;> linarith',
    ]
    lines += ['· ' + inclusion, '· ' + '\n  '.join(reverse)]
    return '\n'.join(lines)


def rank_proof(m: Matrix, kind: str = 'eq') -> str:
    """Return a proof of `A.rank = r`, `r ≤ A.rank` or `A.rank ≤ r` for the rank `r` Sage computes.

    The lower bound comes from a non-singular minor, the upper bound from the height, the width, or a factorisation
    `A = B * C` through the reduced echelon form.

    Args:
        m: The matrix.
        kind: `eq`, `ge` (`r ≤ A.rank`) or `le` (`A.rank ≤ r`).

    Returns:
        The tactic text.

    Raises:
        CertificateError: If the kind is unknown.

    Examples:
        >>> rank_proof(matrix(QQ, [[1, 2, 3], [2, 4, 6]]), 'le').startswith(
        ...     'exact Veriphy.Linear.rank_le_of_factor _ !![1; 2] !![1, 2, 3]')
        True
    """
    r = m.rank()
    if kind not in ('eq', 'ge', 'le'):
        message = f'unknown rank goal {kind!r}; use eq, ge or le'
        raise CertificateError(message)
    if r == m.nrows():
        upper = 'exact Matrix.rank_le_height _'
    elif r == m.ncols():
        upper = 'exact Matrix.rank_le_width _'
    else:
        b, c = rank_factorization(m)
        upper = (
            f'exact Veriphy.Linear.rank_le_of_factor _ {lean_matrix(b)} {lean_matrix(c)} '
            f'(by ext i j <;> fin_cases i <;> fin_cases j <;> {ENTRIES})'
        )
    rows, cols = nonzero_minor(m, r)
    lower = f'exact Veriphy.Linear.le_rank_of_minor _ {_indices(rows)} {_indices(cols)} (by {DET_NONZERO})'
    if kind == 'le':
        return upper
    if kind == 'ge':
        return lower
    return f'apply le_antisymm\n· {upper}\n· {lower}'


def span_dimension_proof(vectors: Sequence[Sequence[object]], field: str = 'ℚ') -> str:
    """Return a proof of `finrank K (span K (range v)) = r` for an explicit family, `r` its rank.

    An independent family's span has its size (`Veriphy.Linear.finrank_span_of_minor`); a dependent family's span
    is first rewritten to the span of an echelon basis.

    Args:
        vectors: The family, as the goal states it.
        field: The scalars.

    Returns:
        The tactic text.
    """
    m = matrix(QQ, vectors)
    if m.rank() == m.nrows():
        _, cols = nonzero_minor(m, m.nrows())
        return f'exact Veriphy.Linear.finrank_span_of_minor _ {_indices(cols)} (by {DET_NONZERO})'
    basis = [list(row) for row in m.rref().rows()[: m.rank()]]
    _, cols = nonzero_minor(matrix(QQ, basis), len(basis))
    equality = span_proof(vectors, other=basis, field=field).replace('\n', '\n  ')
    return '\n'.join(
        [
            (
                f'have hspan : Submodule.span {field} (Set.range {lean_family(vectors, field)}) = '
                f'Submodule.span {field} (Set.range {lean_family(basis, field)}) := by'
            ),
            f'  {equality}',
            'rw [hspan]',
            f'exact Veriphy.Linear.finrank_span_of_minor _ {_indices(cols)} (by {DET_NONZERO})',
        ],
    )


def intersection_dimension_proof(
    first: Sequence[Sequence[object]],
    second: Sequence[Sequence[object]],
    field: str = 'ℚ',
) -> str:
    """Return a proof of `finrank K (span (range v) ⊓ span (range w)) = d` for independent families.

    A basis of the intersection (computed in Sage) gives the lower bound, an independent subfamily of the
    concatenation gives `dim (U ⊔ W)`, and `Veriphy.Linear.finrank_inf_of_bounds` concludes by the dimension formula.

    Args:
        first: An independent family spanning `U`.
        second: An independent family spanning `W`.
        field: The scalars.

    Returns:
        The tactic text.

    Raises:
        CertificateError: If a family is dependent.
    """
    u, w = matrix(QQ, first), matrix(QQ, second)
    if u.rank() != u.nrows() or w.rank() != w.nrows():
        message = 'both families must be independent; reduce each to a basis first'
        raise CertificateError(message)
    common = [list(b) for b in u.row_space().intersection(w.row_space()).basis()]
    joined = [*map(list, first), *map(list, second)]
    pivots = list(matrix(QQ, joined).transpose().pivots())
    sup = [joined[i] for i in pivots]

    def span_size(vectors: Sequence[Sequence[object]]) -> str:
        if not vectors:
            return 'by simp'
        _, cols = nonzero_minor(matrix(QQ, vectors), len(vectors))
        return f'(Veriphy.Linear.finrank_span_of_minor _ {_indices(cols)} (by {DET_NONZERO}))'

    def in_both(v: Sequence[object]) -> str:
        return f'Submodule.mem_inf.2 ⟨{_membership(v, first, field)}, {_membership(v, second, field)}⟩'

    def in_sup(index: int) -> str:
        side, position = ('left', index) if index < len(first) else ('right', index - len(first))
        return f'Submodule.mem_sup_{side} (Submodule.subset_span ⟨{position}, rfl⟩)'

    lower = _span_le(common, in_both).replace('\n', '\n  ') if common else 'simp'
    upper = '\n'.join(
        ['rw [Submodule.span_le]', 'rintro _ ⟨i, rfl⟩', 'fin_cases i', *(f'· exact {in_sup(i)}' for i in pivots)],
    ).replace('\n', '\n  ')
    x_text = f'(Submodule.span {field} (Set.range {lean_family(common, field)}))' if common else '⊥'
    return '\n'.join(
        [
            f'refine Veriphy.Linear.finrank_inf_of_bounds _ _ {x_text}',
            f'  (Submodule.span {field} (Set.range {lean_family(sup, field)}))',
            f'  {span_size(first)}',
            f'  {span_size(second)}',
            f'  ?_ {span_size(common)} ?_ {span_size(sup)} (by norm_num)',
            f'· {lower}',
            f'· {upper}',
        ],
    )


def nonlinearity_proof(g: Callable[..., RingElement], arity: int = 1) -> str:
    """Return a proof of `¬ ∃ f : K →ₗ[K] K, ∀ x, f x = g x` at the points where `g` fails linearity.

    A bilinear map (`arity=2`, `¬ ∃ f : V →ₗ W →ₗ K, ∀ x y, f x y = g x y`) is refuted at `f 0 0 = 0`.

    Args:
        g: The map, a Python function on Sage values.
        arity: 1 for a linear map, 2 for a bilinear one.

    Returns:
        The tactic text.

    Raises:
        CertificateError: If a bilinear map vanishes at zero (only that failure is certified).

    Examples:
        >>> print(nonlinearity_proof(lambda x: x ** 2))
        rintro ⟨f, hf⟩
        have h := f.map_smul (2 : _) (1 : _)
        rw [hf, hf] at h
        norm_num at h
    """
    if arity == BILINEAR:
        if SR(g(0, 0)) == 0:
            message = 'the bilinear map vanishes at zero; only a non-zero value at zero is certified'
            raise CertificateError(message)
        return 'rintro ⟨f, hf⟩\nhave h := hf 0 0\nsimp at h'
    law, points = nonlinearity_witness(g)
    if law == 'map_zero':
        return 'rintro ⟨f, hf⟩\nhave h := hf 0\nsimp at h'
    a, b = (_q(p) for p in points)
    if law == 'map_smul':
        return f'rintro ⟨f, hf⟩\nhave h := f.map_smul ({a} : _) ({b} : _)\nrw [hf, hf] at h\nnorm_num at h'
    return f'rintro ⟨f, hf⟩\nhave h := f.map_add ({a} : _) ({b} : _)\nrw [hf, hf, hf] at h\nnorm_num at h'


def signature_proof(s: Matrix) -> str:
    """Return a proof of `Veriphy.Linear.HasSignature S p q z` with the counts of a congruence Sage computes.

    Args:
        s: The symmetric matrix.

    Returns:
        The tactic text; the counts are those of `signature(symmetric_congruence(s)[1])`.
    """
    p, d = symmetric_congruence(s)
    return '\n'.join(
        [
            f'refine ⟨{lean_matrix(p)}, {lean_vector(d)}, ?_, ?_, ?_, ?_, ?_⟩',
            f'· {DET_NONZERO}',
            f'· ext i j <;> fin_cases i <;> fin_cases j <;> {ENTRIES}',
            'all_goals decide +kernel',
        ],
    )
