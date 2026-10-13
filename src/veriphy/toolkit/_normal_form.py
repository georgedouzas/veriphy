"""Matrix normal forms with certificates: Smith forms over ℤ, Jordan forms and diagonalizations over ℚ.

Each normal form reaches Lean as identities between explicit matrices that the kernel checks: `U * A * V = D` with the
inverses of `U` and `V` (so they are unimodular), or `A * P = P * J` with the inverse of `P` (so `P⁻¹ * A * P = J`).
"""

from sage.all import QQ, ZZ, matrix
from sage.matrix.matrix0 import Matrix

from veriphy.core import CertificateError
from veriphy.toolkit._lean import Lean, tactic
from veriphy.toolkit._lie import rational_matrix_term

PRODUCT = 'VeriphyCheck.mul_eq_of_check (by decide +kernel)'
PRODUCTS = 'VeriphyCheck.mul_eq_mul_of_check (by decide +kernel)'
EQUAL = 'VeriphyCheck.eq_of_check (by decide +kernel)'


def smith_certificate(a: Matrix) -> tuple[Matrix, Matrix, Matrix, Lean]:
    """Return the Smith normal form `D = U A V` of a square integer matrix, with facts proving it.

    Args:
        a: A square integer matrix.

    Returns:
        `D`, `U`, `V` and the facts `hsmith : U * A * V = D`, `hU : U * U⁻¹ = 1`, `hV : V * V⁻¹ = 1` (the inverses
        are integer matrices, so `U` and `V` are unimodular).

    Raises:
        CertificateError: If the matrix is not square and integral.

    Examples:
        >>> d, u, v, facts = smith_certificate(matrix(ZZ, [[2, 4], [6, 8]]))
        >>> d.diagonal()
        [2, 4]
    """
    if not a.is_square() or not all(x in ZZ for x in a.list()):
        message = 'the Smith form certificate needs a square integer matrix'
        raise CertificateError(message)
    d, u, v = matrix(ZZ, a).smith_form()
    terms = {name: rational_matrix_term(m, 'ℤ') for name, m in (('A', a), ('D', d), ('U', u), ('V', v))}
    facts = [
        f'have hsmith : {terms["U"]} * {terms["A"]} * {terms["V"]} = {terms["D"]} := {EQUAL}',
        f'have hU : {terms["U"]} * {rational_matrix_term(u.inverse(), "ℤ")} = 1 := {PRODUCT}',
        f'have hV : {terms["V"]} * {rational_matrix_term(v.inverse(), "ℤ")} = 1 := {PRODUCT}',
    ]
    return d, u, v, tactic('\n'.join(facts))


def jordan_certificate(a: Matrix) -> tuple[Matrix, Matrix, Lean]:
    """Return the Jordan form `J = P⁻¹ A P` of a rational matrix with rational eigenvalues, with facts proving it.

    A diagonalizable matrix gets a diagonal `J`: this is its diagonalization.

    Args:
        a: A square rational matrix whose eigenvalues are rational.

    Returns:
        `J`, `P` and the facts `hjordan : A * P = P * J` and `hP : P * P⁻¹ = 1`.

    Raises:
        CertificateError: If an eigenvalue is not rational (work over a number field instead).

    Examples:
        >>> j, p, facts = jordan_certificate(matrix(QQ, [[2, 1], [0, 2]]))
        >>> j
        [2 1]
        [0 2]
    """
    a = matrix(QQ, a)
    if not a.charpoly().is_constant() and any(f.degree() > 1 for f, _ in a.charpoly().factor()):
        message = f'the eigenvalues are not all rational (characteristic polynomial {a.charpoly().factor()})'
        raise CertificateError(message)
    j, p = a.jordan_form(transformation=True, subdivide=False)
    term_a, term_j, term_p = (rational_matrix_term(m) for m in (a, j, p))
    facts = [
        f'have hjordan : {term_a} * {term_p} = {term_p} * {term_j} := {PRODUCTS}',
        f'have hP : {term_p} * {rational_matrix_term(p.inverse())} = 1 := {PRODUCT}',
    ]
    return j, p, tactic('\n'.join(facts))
