"""Lie superalgebras: graded brackets of supermatrices, the exceptional families, and super-Jacobi certificates.

Two sources of superalgebras:

- supermatrices of a `(m|n)` grading (`sl(1|1)`, `osp(1|2)`), whose graded commutator, supertrace form and Casimir
  are computed directly, every relation a kernel-checked matrix identity;
- the construction `g = g₀ ⊕ V` from a Lie algebra `g₀` acting on `V` with an invariant symplectic form `ω`: the odd
  bracket is the moment map `[v, w] = Σₛ kₛ μₛ(v, w)` over the simple factors of `g₀`, and the super-Jacobi
  identity on three odd vectors is linear in the coefficients `kₛ`, which Sage solves for. This gives `D(2,1;α)`
  (a one-parameter family), `G(3)` and `F(4)`.

Lean receives structure constants with their parities and checks the super-Jacobi identity on every basis triple
with `VeriphyCheck.superJacobi_of_check`; for the family `D(2,1;α)`, three rational values of `α` prove it for all.
"""

import itertools
from collections.abc import Sequence

from sage.all import QQ, ZZ, LieAlgebra, factor, identity_matrix, matrix, vector
from sage.matrix.matrix0 import Matrix

from veriphy.core import CertificateError
from veriphy.toolkit._lean import Lean, tactic
from veriphy.toolkit._lie import Table, smul_combination, structure_constants

EPSILON = matrix(QQ, [[0, 1], [-1, 0]])
SL2 = [matrix(QQ, [[0, 1], [0, 0]]), matrix(QQ, [[0, 0], [1, 0]]), matrix(QQ, [[1, 0], [0, -1]])]
SO7_VECTOR = 7


def graded_commutator(x: Matrix, y: Matrix, px: int, py: int) -> Matrix:
    """Return `x y - (-1)^(|x||y|) y x`.

    Args:
        x: A homogeneous supermatrix.
        y: Another.
        px: The parity of `x` (0 even, 1 odd).
        py: The parity of `y`.

    Returns:
        The graded commutator.
    """
    return x * y - (-1) ** (px * py) * y * x


def supertrace(m: Matrix, even_dim: int) -> object:
    """Return the supertrace `tr A - tr D` of a supermatrix `[[A, B], [C, D]]` with `A` of size `even_dim`.

    Args:
        m: The supermatrix.
        even_dim: The dimension of the even part.

    Returns:
        The supertrace.

    Examples:
        >>> supertrace(identity_matrix(QQ, 3), 1)
        -1
    """
    return sum(m[i, i] for i in range(even_dim)) - sum(m[i, i] for i in range(even_dim, m.nrows()))


def parity_of(m: Matrix, even_dim: int) -> int:
    """Return the parity of a homogeneous supermatrix: 0 when block diagonal, 1 when block off-diagonal.

    Args:
        m: The supermatrix.
        even_dim: The dimension of the even part.

    Returns:
        The parity.

    Raises:
        CertificateError: If the matrix is not homogeneous.
    """
    n = m.nrows()
    even = all(m[i, j] == 0 for i in range(n) for j in range(n) if (i < even_dim) != (j < even_dim))
    odd = all(m[i, j] == 0 for i in range(n) for j in range(n) if (i < even_dim) == (j < even_dim))
    if even and not odd:
        return 0
    if odd and not even:
        return 1
    message = 'the supermatrix is not homogeneous (both its diagonal and off-diagonal blocks are nonzero)'
    raise CertificateError(message)


def super_structure_constants(basis: Sequence[Matrix], parities: Sequence[int]) -> Table:
    """Return the structure constants of the graded commutator on a basis of supermatrices.

    Args:
        basis: Homogeneous supermatrices.
        parities: Their parities.

    Returns:
        `c[i][j][k]`, the coefficient of `eₖ` in `[eᵢ, eⱼ}`.

    Raises:
        CertificateError: If a bracket leaves the span, or has the wrong parity (naming the pair).

    Examples:
        >>> h, e = matrix(QQ, [[1, 0], [0, 1]]), matrix(QQ, [[0, 1], [0, 0]])
        >>> f = matrix(QQ, [[0, 0], [1, 0]])
        >>> c = super_structure_constants([h, e, f], [0, 1, 1])
        >>> c[1][2]
        [1, 0, 0]
    """
    rows = matrix([m.list() for m in basis])
    if rows.rank() < len(basis):
        message = 'the basis supermatrices are linearly dependent'
        raise CertificateError(message)
    table: Table = []
    for i, (a, pa) in enumerate(zip(basis, parities, strict=True)):
        table.append([])
        for j, (b, pb) in enumerate(zip(basis, parities, strict=True)):
            bracket = graded_commutator(a, b, pa, pb)
            try:
                coefficients = list(rows.solve_left(vector(bracket.list())))
            except ValueError:
                message = f'the basis is not closed under the graded bracket: [e{i}, e{j}}} is not in its span'
                raise CertificateError(message) from None
            if any(c != 0 and parities[k] != (pa + pb) % 2 for k, c in enumerate(coefficients)):
                message = f'[e{i}, e{j}}} has the wrong parity'
                raise CertificateError(message)
            table[i].append(coefficients)
    return table


def supertrace_form(basis: Sequence[Matrix], even_dim: int) -> Matrix:
    """Return the supertrace form `B[i][j] = str(eᵢ eⱼ)` of a basis of supermatrices.

    Args:
        basis: Homogeneous supermatrices.
        even_dim: The dimension of the even part of the superspace.

    Returns:
        The form's matrix.
    """
    return matrix(QQ, [[supertrace(a * b, even_dim) for b in basis] for a in basis])


def super_casimir(basis: Sequence[Matrix], parities: Sequence[int], form: Matrix) -> Matrix:
    """Return the quadratic Casimir `Σ (B⁻¹) eᵢ eⱼ` for an invariant form, checked to commute with every basis element.

    The order of the inverse form's indices differs between conventions for superalgebras; Sage tries both and keeps
    the one that commutes.

    Args:
        basis: Homogeneous supermatrices.
        parities: Their parities.
        form: An invariant nondegenerate form on the basis.

    Returns:
        The Casimir (an even supermatrix).

    Raises:
        CertificateError: If the form is degenerate, or neither ordering commutes.
    """
    if form.det() == 0:
        message = 'the invariant form is degenerate'
        raise CertificateError(message)
    inverse = form.inverse()
    n = len(basis)
    for transposed in (False, True):
        c = sum(
            (
                (inverse[j, i] if transposed else inverse[i, j]) * basis[i] * basis[j]
                for i in range(n)
                for j in range(n)
            ),
            0 * basis[0],
        )
        if all(c * x == x * c for x in basis):
            return c
    message = 'no ordering of the inverse form gives a commuting Casimir (is the form invariant?)'
    raise CertificateError(message)


def super_jacobi_violations(table: Table, parities: Sequence[int]) -> list[tuple[int, int, int, int]]:
    """Return the basis triples and coordinates `(i, j, k, m)` where the super-Jacobi identity fails.

    The identity is `(-1)^(|i||k|) [eᵢ, [eⱼ, eₖ}} + (-1)^(|j||i|) [eⱼ, [eₖ, eᵢ}} + (-1)^(|k||j|) [eₖ, [eᵢ, eⱼ}} = 0`.

    Args:
        table: Structure constants.
        parities: The basis parities.

    Returns:
        The violations, empty for a Lie superalgebra.
    """
    n = len(table)
    support = [[[(ell, x) for ell, x in enumerate(table[i][j]) if x != 0] for j in range(n)] for i in range(n)]

    def nested(a: int, b: int, c: int) -> list[object]:
        result = [0] * n
        for ell, x in support[b][c]:
            for m, y in support[a][ell]:
                result[m] += x * y
        return result

    violations = []
    for i, j, k in itertools.product(range(n), repeat=3):
        p = parities
        terms = [
            ((-1) ** (p[i] * p[k]), nested(i, j, k)),
            ((-1) ** (p[j] * p[i]), nested(j, k, i)),
            ((-1) ** (p[k] * p[j]), nested(k, i, j)),
        ]
        for m in range(n):
            if sum(s * t[m] for s, t in terms) != 0:
                violations.append((i, j, k, m))
    return violations


def invariant_forms(ops: Sequence[Matrix], *, symmetric: bool) -> list[Matrix]:
    """Return a basis of the bilinear forms `B` with `Tᵀ B + B T = 0` for every `T`, symmetric or antisymmetric.

    Args:
        ops: Matrices acting on one space.
        symmetric: Whether to look for symmetric (otherwise antisymmetric) forms.

    Returns:
        The forms.
    """
    d = ops[0].nrows()
    equations = []
    for t in ops:
        # the entries of Tᵀ B + B T, as linear functions of the entries of B (row-major)
        equations.append(
            t.transpose().tensor_product(identity_matrix(QQ, d)) + identity_matrix(QQ, d).tensor_product(t.transpose()),
        )
    sign = -1 if symmetric else 1
    swap = matrix(QQ, d * d, d * d, lambda r, c: 1 if c == (r % d) * d + r // d else 0)
    equations.append(identity_matrix(QQ, d * d) + sign * swap)
    system = matrix(QQ, [row for block in equations for row in block.rows()])
    return [matrix(QQ, d, d, list(b)) for b in system.right_kernel().basis()]


def _moment_maps(even_ops: Sequence[Matrix], factors: Sequence[int], omega: Matrix) -> list[list[list[list[object]]]]:
    """Return, per simple factor, the moment map `μₛ(vᵢ, vⱼ)` as coefficients on the even basis."""
    d = omega.nrows()
    result = []
    for s in sorted(set(factors)):
        members = [a for a, f in enumerate(factors) if f == s]
        gram = matrix(QQ, [[(even_ops[a] * even_ops[b]).trace() for b in members] for a in members])
        inverse = gram.inverse()
        mu = [[[0] * len(even_ops) for _ in range(d)] for _ in range(d)]
        for i, j in itertools.product(range(d), repeat=2):
            v, w = identity_matrix(QQ, d).column(i), identity_matrix(QQ, d).column(j)
            pairing = [v * omega * (even_ops[b] * w) for b in members]
            for a_index, a in enumerate(members):
                mu[i][j][a] = sum(inverse[a_index, b_index] * pairing[b_index] for b_index in range(len(members)))
        result.append(mu)
    return result


def _assemble(even_ops: Sequence[Matrix], moments: Sequence[object], coefficients: Sequence[object]) -> Table:
    """Return the structure constants of `g₀ ⊕ V` for given coefficients of the moment maps."""
    even_table = structure_constants(even_ops)
    n0, d = len(even_ops), even_ops[0].nrows()
    n = n0 + d
    table = [[[QQ(0)] * n for _ in range(n)] for _ in range(n)]
    for a, b in itertools.product(range(n0), repeat=2):
        for k in range(n0):
            table[a][b][k] = QQ(even_table[a][b][k])
    for a in range(n0):
        for i in range(d):
            for j in range(d):
                # [T, vᵢ] = T vᵢ, [vᵢ, T] = -T vᵢ
                table[a][n0 + i][n0 + j] = QQ(even_ops[a][j, i])
                table[n0 + i][a][n0 + j] = -QQ(even_ops[a][j, i])
    for i, j in itertools.product(range(d), repeat=2):
        for k in range(n0):
            table[n0 + i][n0 + j][k] = sum(c * mu[i][j][k] for c, mu in zip(coefficients, moments, strict=True))
    return table


def moment_coefficients(even_ops: Sequence[Matrix], factors: Sequence[int], omega: Matrix) -> list[list[object]]:
    """Return a basis of the coefficients `kₛ` for which the moment-map bracket satisfies super-Jacobi on `V`.

    Args:
        even_ops: A basis of `g₀`, as matrices acting faithfully on `V`.
        factors: The simple factor of each basis element.
        omega: An invariant antisymmetric form on `V`.

    Returns:
        The solutions (one for `G(3)` and `F(4)`, two for the family `D(2,1;α)`).
    """
    moments = _moment_maps(even_ops, factors, omega)
    d, n0 = omega.nrows(), len(even_ops)
    rows = []
    for i, j, k in itertools.product(range(d), repeat=3):
        for m in range(d):
            # Σ_cyclic [vᵢ, [vⱼ, vₖ]] at vₘ, for each factor's moment map: [vᵢ, T] = -T vᵢ
            row = []
            for mu in moments:
                total = 0
                for x, y, z in ((i, j, k), (j, k, i), (k, i, j)):
                    total -= sum(mu[y][z][a] * even_ops[a][m, x] for a in range(n0))
                row.append(total)
            rows.append(row)
    return [list(b) for b in matrix(QQ, rows).right_kernel().basis()]


def contragredient_superalgebra(
    even_ops: Sequence[Matrix],
    factors: Sequence[int],
    omega: Matrix,
    coefficients: Sequence[object] | None = None,
) -> tuple[Table, list[int]]:
    """Return the structure constants and parities of `g₀ ⊕ V` with the moment-map odd bracket.

    Args:
        even_ops: A basis of `g₀`, as matrices acting faithfully on `V`.
        factors: The simple factor of each basis element.
        omega: An invariant antisymmetric form on `V`.
        coefficients: The moment-map coefficients `kₛ`; Sage's unique solution when `None`.

    Returns:
        The table (even basis first, then the basis of `V`) and the parities.

    Raises:
        CertificateError: If the coefficients are not unique (a family; pass them), or no bracket exists.
    """
    if coefficients is None:
        solutions = moment_coefficients(even_ops, factors, omega)
        if len(solutions) != 1:
            message = f'{len(solutions)} independent moment-map coefficients satisfy super-Jacobi; pass them'
            raise CertificateError(message)
        coefficients = solutions[0]
    table = _assemble(even_ops, _moment_maps(even_ops, factors, omega), coefficients)
    return table, [0] * len(even_ops) + [1] * omega.nrows()


def _kron(*ms: Matrix) -> Matrix:
    """Return the Kronecker product of matrices."""
    result = ms[0]
    for m in ms[1:]:
        result = result.tensor_product(m)
    return result


def d21_alpha(alpha: object) -> tuple[Table, list[int]]:
    """Return `D(2,1;α)`: `sl2³` on `2 ⊗ 2 ⊗ 2`, with moment-map coefficients `(1, α, -1 - α)`.

    Args:
        alpha: The parameter (rational, or an element of a field of rational functions).

    Returns:
        The structure constants (17-dimensional, 9 even and 8 odd) and the parities.

    Examples:
        >>> table, parities = d21_alpha(QQ(2))
        >>> len(table), sum(parities), super_jacobi_violations(table, parities)
        (17, 8, [])
    """
    one = identity_matrix(QQ, 2)
    even = [_kron(s, one, one) for s in SL2] + [_kron(one, s, one) for s in SL2] + [_kron(one, one, s) for s in SL2]
    factors = [0] * 3 + [1] * 3 + [2] * 3
    omega = _kron(EPSILON, EPSILON, EPSILON)
    moments = _moment_maps(even, factors, omega)
    table = _assemble(even, moments, [1, alpha, -1 - alpha])
    return table, [0] * 9 + [1] * 8


def g3() -> tuple[Table, list[int]]:
    """Return `G(3)`: `G₂ ⊕ sl2` on `7 ⊗ 2` (31-dimensional, 17 even and 14 odd).

    Returns:
        The structure constants and parities.
    """
    g2 = [matrix(QQ, b.value) for b in LieAlgebra(QQ, cartan_type=['G', 2], representation='matrix').basis()]
    (form,) = invariant_forms(g2, symmetric=True)
    even = [_kron(t, identity_matrix(QQ, 2)) for t in g2] + [_kron(identity_matrix(QQ, 7), s) for s in SL2]
    return contragredient_superalgebra(even, [0] * len(g2) + [1] * 3, _kron(form, EPSILON))


def so7_spinor_gammas() -> list[Matrix]:
    """Return seven anticommuting real antisymmetric 8 by 8 matrices squaring to `-1` (the spinor of so(7)).

    Returns:
        The gamma matrices, tensor products of `1`, `σ₁`, `σ₃` and `ε` with an odd number of `ε`
        (`Cl(0,7)` is real, of dimension 8 on each of its two summands).

    Raises:
        CertificateError: If no such set is found (it always is).
    """
    one, x, z = identity_matrix(QQ, 2), matrix(QQ, [[0, 1], [1, 0]]), matrix(QQ, [[1, 0], [0, -1]])
    candidates = []
    for factors in itertools.product([one, x, z, EPSILON], repeat=3):
        m = _kron(*factors)
        if m.is_skew_symmetric() and m * m == -identity_matrix(QQ, 8):
            candidates.append(m)

    def extend(chosen: list[Matrix], start: int) -> list[Matrix] | None:
        if len(chosen) == SO7_VECTOR:
            return chosen
        for k in range(start, len(candidates)):
            g = candidates[k]
            if all(g * h + h * g == 0 for h in chosen):
                found = extend([*chosen, g], k + 1)
                if found is not None:
                    return found
        return None

    gammas = extend([], 0)
    if gammas is None:
        message = 'no Clifford basis found'
        raise CertificateError(message)
    return gammas


def f4() -> tuple[Table, list[int]]:
    """Return `F(4)`: `so(7) ⊕ sl2` on `8 ⊗ 2`, the spinor tensor the doublet (40-dimensional, 24 even, 16 odd).

    Returns:
        The structure constants and parities.
    """
    gammas = so7_spinor_gammas()
    so7 = [gammas[i] * gammas[j] / 2 for i, j in itertools.combinations(range(7), 2)]
    even = [_kron(t, identity_matrix(QQ, 2)) for t in so7] + [_kron(identity_matrix(QQ, 8), s) for s in SL2]
    return contragredient_superalgebra(even, [0] * len(so7) + [1] * 3, _kron(identity_matrix(QQ, 8), EPSILON))


def _parities_term(parities: Sequence[int]) -> str:
    """Return the parities as a Lean `Fin n → Bool`."""
    return f'(![{", ".join("true" if p else "false" for p in parities)}] : Fin {len(parities)} → Bool)'


def sparse_rows_term(table: Table, ring: str | None = None) -> str:
    """Return the rows of a table, the nonzero `(k, c)` of each `[eᵢ, eⱼ}`, as a Lean term.

    Args:
        table: Rational structure constants.
        ring: `ℤ` or `ℚ`; `ℤ` when every constant is an integer and `None` is given.

    Returns:
        The term `Fin n → Fin n → List (Fin n × R)`.

    Examples:
        >>> rows = sparse_rows_term([[[0, 0], [0, 1]], [[0, -1], [0, 0]]])
        >>> rows.startswith('(fun (i j : Fin 2) => ((([[[], [(1, 1)]], [[(1, -1)], []]] : List (List (List (Fin 2 × ℤ')
        True
    """
    n = len(table)
    integral = all(QQ(c).denominator() == 1 for plane in table for row in plane for c in row)
    chosen = ring or ('ℤ' if integral else 'ℚ')

    def coefficient(c: object) -> str:
        q = QQ(c)
        return str(q) if q.denominator() == 1 else f'{q.numerator()} / {q.denominator()}'

    def row(entries: Sequence[object]) -> str:
        return '[' + ', '.join(f'({k}, {coefficient(c)})' for k, c in enumerate(entries) if c != 0) + ']'

    # nested lists indexed by `i.val`: the kernel walks a list literal faster than it unfolds `![…]` vectors
    rows = ', '.join('[' + ', '.join(row(table[i][j]) for j in range(n)) + ']' for i in range(n))
    entry = f'Fin {n} × {chosen}'
    return f'(fun (i j : Fin {n}) => ((([{rows}] : List (List (List ({entry})))).getD i.val []).getD j.val []))'


def integral_rescaling(table: Table, parities: Sequence[int]) -> tuple[Table, tuple[int, int]]:
    """Rescale the basis (even elements by `μ`, odd by `λ`) so that every structure constant is an integer.

    With `eᵢ' = sᵢ eᵢ` the constants become `sᵢ sⱼ / sₖ cᵢⱼₖ`: even-even and even-odd ones scale by `μ`, odd-odd ones
    by `λ² / μ`. Integer constants make the kernel check faster.

    Args:
        table: Rational structure constants.
        parities: The basis parities.

    Returns:
        The rescaled table and `(μ, λ)`.
    """
    n = len(table)
    mixed, odd = ZZ(1), ZZ(1)
    for i, j, k in itertools.product(range(n), repeat=3):
        d = QQ(table[i][j][k]).denominator()
        if parities[i] and parities[j]:
            odd = odd.lcm(d)
        else:
            mixed = mixed.lcm(d)
    mu = mixed
    # the smallest λ with λ² divisible by μ times the odd-odd denominators
    lam = ZZ(1)
    for prime, exponent in factor(mu * odd):
        lam *= prime ** ((exponent + 1) // 2)
    scale = [lam if p else mu for p in parities]
    rescaled = [
        [[table[i][j][k] * scale[i] * scale[j] / scale[k] for k in range(n)] for j in range(n)] for i in range(n)
    ]
    return rescaled, (int(mu), int(lam))


def super_jacobi_certificate(table: Table, parities: Sequence[int], name: str = 'hsuper') -> Lean:
    """Return a fact that the structure constants satisfy the super-Jacobi identity on every basis triple.

    Sage checks it first; the kernel checks it again on the sparse table (`VeriphyCheck.Sparse.superJacobiCheck`),
    at a cost that follows the nonzero products of constants.

    Args:
        table: Rational structure constants (integers check fastest; see `integral_rescaling`).
        parities: The basis parities.
        name: The fact's name.

    Returns:
        The fact `∀ i j k m, VeriphyCheck.superJacobiAt (VeriphyCheck.Sparse.table r) p i j k m = 0`.

    Raises:
        CertificateError: If the identity fails in Sage, naming a violation.
    """
    violations = super_jacobi_violations(table, parities)
    if violations:
        message = f'super-Jacobi fails at (i, j, k, m) = {violations[0]} and {len(violations) - 1} other places'
        raise CertificateError(message)
    return tactic(
        f'have {name} := VeriphyCheck.Sparse.superJacobi_of_check (r := {sparse_rows_term(table)}) '
        f'(p := {_parities_term(parities)}) (by decide +kernel)',
    )


def super_jacobi_family_certificate(
    table0: Table,
    table1: Table,
    parities: Sequence[int],
    name: str = 'hfamily',
    field: str = 'ℝ',
) -> Lean:
    """Return a fact that `c₀ + α c₁` satisfies super-Jacobi for every `α` in any field of characteristic zero.

    The super-Jacobi sums are quadratic in `α`, so the kernel checks at `α = 0`, `1` and `-1` decide them.

    Args:
        table0: The constant part of the structure constants.
        table1: The part linear in `α`.
        parities: The basis parities.
        name: The fact's name.
        field: The field of characteristic zero `α` ranges over.

    Returns:
        The fact `∀ α i j k m, VeriphyCheck.superJacobiAt (c₀ + α c₁) p i j k m = 0`, over the sparse tables.

    Raises:
        CertificateError: If the identity fails in Sage at one of the three values.
    """
    n = len(table0)
    for t in (0, 1, -1):
        shifted = [[[table0[i][j][k] + t * table1[i][j][k] for k in range(n)] for j in range(n)] for i in range(n)]
        if super_jacobi_violations(shifted, parities):
            message = f'super-Jacobi fails at α = {t}'
            raise CertificateError(message)
    checks = ' '.join(['(by decide +kernel)'] * 3)
    return tactic(
        f'have {name} := VeriphyCheck.Sparse.superJacobi_affine (r₀ := {sparse_rows_term(table0, "ℚ")}) '
        f'(r₁ := {sparse_rows_term(table1, "ℚ")}) (p := {_parities_term(parities)}) {checks} (K := {field})',
    )


def super_relations(basis: Sequence[Matrix], parities: Sequence[int], names: Sequence[str]) -> Lean:
    """Return facts stating each graded bracket of a basis of supermatrices, checked by the kernel.

    An odd pair gets the anticommutator `x * y + y * x = …`, any other the commutator `x * y - y * x = …`.

    Args:
        basis: Homogeneous supermatrices over ℚ.
        parities: Their parities.
        names: Their Lean names (definitions).

    Returns:
        The facts `hs_i_j` for `i ≤ j`.
    """
    table = super_structure_constants(basis, parities)
    lines = []
    for i, j in itertools.combinations_with_replacement(range(len(basis)), 2):
        sign = '+' if parities[i] and parities[j] else '-'
        rhs = smul_combination(table[i][j], names)
        lines.append(
            f'have hs_{i}_{j} : {names[i]} * {names[j]} {sign} {names[j]} * {names[i]} = {rhs} := '
            'VeriphyCheck.eq_of_check (by decide +kernel)',
        )
    return tactic('\n'.join(lines))
