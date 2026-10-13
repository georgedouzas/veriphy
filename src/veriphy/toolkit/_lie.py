"""Lie algebras of explicit matrices: structure constants, invariant forms and Casimirs, with Lean proofs.

Sage computes; Lean checks. Every result reaches Lean as a finite identity between explicit matrices (a bracket
relation, a commutation) or as a structure-constant table that `VeriphyCheck`'s kernel checkers verify.
"""

from collections.abc import Sequence

from sage.all import QQ, matrix, vector
from sage.all import Sequence as SageSequence
from sage.matrix.matrix0 import Matrix

from veriphy.core import CertificateError
from veriphy.toolkit._lean import Lean, tactic
from veriphy.toolkit._reflect import DECIDABLE_CARRIERS, structure_constants_term

Table = list[list[list[object]]]


def _coordinates(basis: Sequence[Matrix]) -> Matrix:
    """Return the basis flattened to the rows of one matrix over a common ring, checking independence."""
    if not basis:
        message = 'the basis is empty'
        raise CertificateError(message)
    ring = SageSequence([entry for m in basis for entry in m.list()]).universe()
    rows = matrix(ring, [m.list() for m in basis])
    if rows.rank() < len(basis):
        message = 'the basis matrices are linearly dependent'
        raise CertificateError(message)
    return rows


def structure_constants(basis: Sequence[Matrix]) -> Table:
    """Return `c[i][j][k]`, the coefficient of `eₖ` in `⁅eᵢ, eⱼ⁆ = eᵢ eⱼ - eⱼ eᵢ`.

    Args:
        basis: Square matrices of one size, over ℚ, a number field or Sage's symbolic ring.

    Returns:
        The table, with entries in the matrices' ring.

    Raises:
        CertificateError: If the basis is dependent, or not closed under the bracket (naming the first pair whose
            bracket leaves the span).

    Examples:
        >>> e, f, h = matrix(QQ, [[0, 1], [0, 0]]), matrix(QQ, [[0, 0], [1, 0]]), matrix(QQ, [[1, 0], [0, -1]])
        >>> c = structure_constants([e, f, h])
        >>> c[2][0], c[2][1], c[0][1]
        ([2, 0, 0], [0, -2, 0], [0, 0, 1])
        >>> structure_constants([e, f])
        Traceback (most recent call last):
        ...
        veriphy.core._errors.CertificateError: the basis is not closed under the bracket: ⁅e0, e1⁆ is not in its span
    """
    rows = _coordinates(basis)
    ring = rows.base_ring()
    table: Table = []
    for i, a in enumerate(basis):
        table.append([])
        for j, b in enumerate(basis):
            bracket = vector(ring, (a * b - b * a).list())
            try:
                solution = rows.solve_left(bracket)
            except ValueError:
                message = f'the basis is not closed under the bracket: ⁅e{i}, e{j}⁆ is not in its span'
                raise CertificateError(message) from None
            table[i].append(list(solution))
    return table


def adjoint_matrices(table: Table) -> list[Matrix]:
    """Return the matrices of `ad eᵢ` in the basis: column `l` holds the coordinates of `⁅eᵢ, eₗ⁆`.

    Args:
        table: Structure constants, as `structure_constants` returns them.

    Returns:
        One matrix per basis element.
    """
    n = len(table)
    ring = SageSequence([x for plane in table for row in plane for x in row]).universe()
    return [matrix(ring, n, n, lambda k, ell, i=i: table[i][ell][k]) for i in range(n)]


def killing_form(table: Table) -> Matrix:
    """Return the Killing form's matrix, `K[i][j] = tr(ad eᵢ ad eⱼ)`.

    Args:
        table: Structure constants.

    Returns:
        The symmetric matrix of the form.

    Examples:
        >>> e, f, h = matrix(QQ, [[0, 1], [0, 0]]), matrix(QQ, [[0, 0], [1, 0]]), matrix(QQ, [[1, 0], [0, -1]])
        >>> killing_form(structure_constants([e, f, h]))
        [0 4 0]
        [4 0 0]
        [0 0 8]
    """
    ads = adjoint_matrices(table)
    return matrix(ads[0].base_ring(), len(ads), len(ads), lambda i, j: (ads[i] * ads[j]).trace())


def trace_form(basis: Sequence[Matrix]) -> Matrix:
    """Return the trace form of the representation, `B[i][j] = tr(eᵢ eⱼ)`.

    Args:
        basis: The representation matrices.

    Returns:
        The symmetric matrix of the form.
    """
    ring = _coordinates(basis).base_ring()
    return matrix(ring, len(basis), len(basis), lambda i, j: (basis[i] * basis[j]).trace())


def casimir(basis: Sequence[Matrix], form: Matrix | None = None) -> Matrix:
    """Return the quadratic Casimir `Σᵢⱼ (B⁻¹)ᵢⱼ eᵢ eⱼ` of the representation, for an invariant form `B`.

    Args:
        basis: The representation matrices, a basis of the Lie algebra.
        form: The invariant form's matrix in that basis; the Killing form when `None`.

    Returns:
        The Casimir matrix.

    Raises:
        CertificateError: If the form is degenerate (the Killing form of an algebra that is not semisimple).

    Examples:
        >>> e, f, h = matrix(QQ, [[0, 1], [0, 0]]), matrix(QQ, [[0, 0], [1, 0]]), matrix(QQ, [[1, 0], [0, -1]])
        >>> casimir([e, f, h])
        [3/8   0]
        [  0 3/8]
    """
    b = killing_form(structure_constants(basis)) if form is None else form
    if b.det() == 0:
        message = 'the invariant form is degenerate; pass a nondegenerate one (the algebra may not be semisimple)'
        raise CertificateError(message)
    inverse = b.inverse()
    n = len(basis)
    return sum((inverse[i, j] * basis[i] * basis[j] for i in range(n) for j in range(n)), 0 * basis[0])


def _coefficient(c: object) -> str:
    """Return a scalar's Lean text in a `•` term: an integer, or a rational at type ℚ."""
    q = QQ(c)
    if q.denominator() == 1:
        return str(q)
    return f'({q.numerator()} / {q.denominator()} : ℚ)'


def smul_combination(coefficients: Sequence[object], names: Sequence[str]) -> str:
    """Return the Lean text of `Σ cₖ • nameₖ`, leaving out zero terms and unit coefficients.

    Args:
        coefficients: Rational coefficients.
        names: The Lean terms they multiply.

    Returns:
        The text, `0` when every coefficient is zero.

    Examples:
        >>> smul_combination([2, 0, -1], ['e', 'f', 'h'])
        '2 • e - h'
        >>> smul_combination([QQ(1) / 2, 1], ['x', 'y'])
        '(1 / 2 : ℚ) • x + y'
        >>> smul_combination([0, 0], ['x', 'y'])
        '0'
    """
    text = ''
    for c, name in zip(coefficients, names, strict=True):
        q = QQ(c)
        if q == 0:
            continue
        sign = '-' if q < 0 else '+'
        size = abs(q)
        term = name if size == 1 else f'{_coefficient(size)} • {name}'
        text = (f'-{term}' if sign == '-' else term) if not text else f'{text} {sign} {term}'
    return text or '0'


def _identity_proof(lemma: str, *, bracket: bool, carrier: str, unfold: Sequence[str], size: int, limit: int) -> str:
    """Return a proof of a matrix identity: the kernel checker over ℤ or ℚ, entrywise otherwise."""
    if carrier in DECIDABLE_CARRIERS and size > 0 and limit < size:
        return f'{lemma} (by decide +kernel)'
    steps = [f'unfold {" ".join(unfold)}'] if unfold else []
    if bracket:
        steps.append('rw [Ring.lie_def]')
    steps += ['ext i j', 'fin_cases i <;> fin_cases j <;> norm_num [Matrix.mul_apply, Fin.sum_univ_succ]']
    return 'by\n' + '\n'.join(f'  {s}' for s in steps)


def bracket_relations(
    basis: Sequence[Matrix],
    names: Sequence[str],
    *,
    carrier: str = 'ℚ',
    definitions: bool = True,
    pairs: Sequence[tuple[int, int]] | None = None,
    entrywise_limit: int = 0,
) -> Lean:
    """Return `have` facts `⁅eᵢ, eⱼ⁆ = Σ cᵢⱼₖ • eₖ` for the basis, each proved in Lean.

    Over ℤ or ℚ the kernel checker `VeriphyCheck.bracket_eq_of_check` proves each relation from the matrices (which
    it unfolds); otherwise the proof is entrywise. The coefficients must be rational.

    Args:
        basis: The basis matrices.
        names: The Lean terms naming them, in the same order (definitions, or matrix literals).
        carrier: The Lean type of the entries.
        definitions: Whether the names are definitions an entrywise proof must unfold.
        pairs: The pairs `(i, j)` to state; every pair `i < j` when `None`.
        entrywise_limit: Prove entrywise up to this dimension even over ℤ or ℚ.

    Returns:
        The facts, named `hb_i_j`.

    Raises:
        CertificateError: If a structure constant is not rational.

    Examples:
        >>> e, f, h = matrix(QQ, [[0, 1], [0, 0]]), matrix(QQ, [[0, 0], [1, 0]]), matrix(QQ, [[1, 0], [0, -1]])
        >>> print(bracket_relations([e, f, h], ['e', 'f', 'h'], pairs=[(2, 0)]))
        have hb_2_0 : ⁅h, e⁆ = 2 • e := VeriphyCheck.bracket_eq_of_check (by decide +kernel)
    """
    table = structure_constants(basis)
    chosen = pairs if pairs is not None else [(i, j) for i in range(len(basis)) for j in range(i + 1, len(basis))]
    size = basis[0].nrows()
    lines = []
    for i, j in chosen:
        coefficients = table[i][j]
        if not all(c in QQ for c in coefficients):
            message = f'⁅{names[i]}, {names[j]}⁆ has non-rational structure constants {coefficients}'
            raise CertificateError(message)
        statement = f'⁅{names[i]}, {names[j]}⁆ = {smul_combination(coefficients, names)}'
        used = [names[i], names[j], *(n for n, c in zip(names, coefficients, strict=True) if QQ(c) != 0)]
        unfold = list(dict.fromkeys(used)) if definitions else []
        proof = _identity_proof(
            'VeriphyCheck.bracket_eq_of_check',
            bracket=True,
            carrier=carrier,
            unfold=unfold,
            size=size,
            limit=entrywise_limit,
        )
        lines.append(f'have hb_{i}_{j} : {statement} := {proof}')
    return tactic('\n'.join(lines))


def commutation_facts(
    element: str,
    names: Sequence[str],
    *,
    size: int,
    carrier: str = 'ℚ',
    definitions: bool = True,
    entrywise_limit: int = 0,
) -> Lean:
    """Return `have` facts `C * eᵢ = eᵢ * C`: the element (a Casimir) commutes with each basis matrix.

    Args:
        element: The Lean term of the commuting matrix (a definition, or a literal).
        names: The Lean terms of the basis matrices.
        size: The matrices' dimension.
        carrier: The Lean type of the entries.
        definitions: Whether the terms are definitions an entrywise proof must unfold.
        entrywise_limit: Prove entrywise up to this dimension even over ℤ or ℚ.

    Returns:
        The facts, named `hc_i`.

    Examples:
        >>> print(commutation_facts('C', ['e'], size=2))
        have hc_0 : C * e = e * C := VeriphyCheck.commute_of_check (by decide +kernel)
    """
    lines = []
    for i, name in enumerate(names):
        unfold = list(dict.fromkeys([element, name])) if definitions else []
        proof = _identity_proof(
            'VeriphyCheck.commute_of_check',
            bracket=False,
            carrier=carrier,
            unfold=unfold,
            size=size,
            limit=entrywise_limit,
        )
        lines.append(f'have hc_{i} : {element} * {name} = {name} * {element} := {proof}')
    return tactic('\n'.join(lines))


def jacobi_certificate(table: Table, name: str = 'hjacobi') -> Lean:
    """Return a fact that the bracket the structure constants define satisfies the Jacobi identity.

    `VeriphyCheck.jacobi_of_check` reduces it, by trilinearity, to the Jacobi identity on basis triples, which the
    kernel checks. With antisymmetry (`VeriphyCheck.bracket_self_of_check`) this certifies a Lie algebra.

    Args:
        table: Rational structure constants.
        name: The fact's name.

    Returns:
        The fact `∀ x y z, ⁅x, ⁅y, z⁆⁆ + ⁅y, ⁅z, x⁆⁆ + ⁅z, ⁅x, y⁆⁆ = 0` for `VeriphyCheck.scBracket`.

    Raises:
        CertificateError: If a structure constant is not rational.

    Examples:
        >>> fact = str(jacobi_certificate([[[0, 0], [0, 1]], [[0, -1], [0, 0]]]))
        >>> fact.startswith('have hjacobi := VeriphyCheck.jacobi_of_check (c := (![![![0, 0], ![0, 1]], ')
        True
    """
    if not all(c in QQ for plane in table for row in plane for c in row):
        message = 'the structure constants are not rational; choose a basis with rational constants'
        raise CertificateError(message)
    table_term = structure_constants_term(table)
    return tactic(f'have {name} := VeriphyCheck.jacobi_of_check (c := {table_term}) (by decide +kernel)')
