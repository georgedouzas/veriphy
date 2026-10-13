"""Closed forms of matrix exponentials, proved against mathlib's `NormedSpace.exp`.

Two routes, chosen by Sage:

- a nilpotent `N` (`Nᵏ = 0`): `exp N = Σ_{n<k} Nⁿ / n!`, from `exp_eq_tsum_rat` and the finite support of the series;
- a matrix `A` diagonalizable over ℚ, `A = P D P⁻¹`: `exp (t • A) = P exp (t • D) P⁻¹`, from `Matrix.exp_conj` and
  `Matrix.exp_diagonal`, and the entries are matched with the goal's (exponentials, `cosh`, `sinh`) by `simp` and
  `ring`.
"""

from sage.all import QQ, SR, diagonal_matrix, factorial, matrix, var
from sage.matrix.matrix0 import Matrix

from veriphy.core import CertificateError
from veriphy.toolkit._lean import Lean, tactic

ENTRY_SIMP = (
    'simp [Matrix.mul_apply, Fin.sum_univ_succ, Matrix.diagonal_apply, Matrix.smul_apply, Matrix.vecMul_diagonal, '
    'Matrix.mulVec_diagonal]'
)


def _rational(q: object) -> str:
    """Return a rational as Lean text."""
    value = QQ(q)
    return str(value) if value.denominator() == 1 else f'({value.numerator()} / {value.denominator()})'


def _literal(m: Matrix) -> str:
    """Return a rational matrix as a `!![…]` literal over ℝ."""
    rows = '; '.join(', '.join(_rational(x) for x in row) for row in m.rows())
    return f'(!![{rows}] : Matrix (Fin {m.nrows()}) (Fin {m.ncols()}) ℝ)'


def nilpotency_index(n: Matrix) -> int | None:
    """Return the least `k` with `Nᵏ = 0`, or `None` when `N` is not nilpotent.

    Args:
        n: A square matrix.

    Returns:
        The index.

    Examples:
        >>> nilpotency_index(matrix(QQ, [[0, 1, 2], [0, 0, 3], [0, 0, 0]]))
        3
    """
    power = matrix.identity(n.base_ring(), n.nrows())
    for k in range(1, n.nrows() + 1):
        power = power * n
        if power == 0:
            return k
    return None


def nilpotent_exponential(n: Matrix) -> tuple[Matrix, Lean]:
    """Return `exp N` for a nilpotent rational matrix, and a proof of `exp N = E` for the goal's `N` and `E`.

    Args:
        n: The nilpotent matrix.

    Returns:
        `E = Σ_{k<index} Nᵏ / k!` and the tactic, which first proves `N ^ index = 0`.

    Raises:
        CertificateError: If `N` is not nilpotent.

    Examples:
        >>> e, proof = nilpotent_exponential(matrix(QQ, [[0, 1, 2], [0, 0, 3], [0, 0, 0]]))
        >>> e
        [  1   1 7/2]
        [  0   1   3]
        [  0   0   1]
    """
    index = nilpotency_index(n)
    if index is None:
        message = 'the matrix is not nilpotent; use diagonalizable_exponential or a Jordan decomposition'
        raise CertificateError(message)
    e = sum((n**k / factorial(k) for k in range(index)), 0 * n)
    lines = [
        f'have hN : {_literal(n)} ^ {index} = 0 := by',
        f'  ext i j; fin_cases i <;> fin_cases j <;> {ENTRY_SIMP.replace("simp [", "simp [pow_succ, ")}',
        'rw [NormedSpace.exp_eq_tsum_rat]',
        'beta_reduce',
        f'rw [tsum_eq_sum (s := Finset.range {index}) (fun n hn => by',
        '  simp only [Finset.mem_range, not_lt] at hn',
        '  rw [pow_eq_zero_of_le hn hN, smul_zero])]',
        'ext i j; fin_cases i <;> fin_cases j <;>',
        f'  {ENTRY_SIMP.replace("simp [", "simp [Finset.sum_range_succ, pow_succ, Rat.smul_def, ")} <;> norm_num',
    ]
    return e, tactic('\n'.join(lines))


def diagonalizable_exponential(a: Matrix, parameter: str = 't') -> tuple[Matrix, Lean]:
    """Return `exp (t • A)` for `A` diagonalizable over ℚ, and a proof of the goal `exp (t • A) = E`.

    The goal's right side may be written with `Real.exp`, `Real.cosh` or `Real.sinh`: the entries are compared after
    unfolding `cosh` and `sinh` into exponentials.

    Args:
        a: A rational matrix with rational eigenvalues and a basis of eigenvectors.
        parameter: The Lean name of the real parameter `t`.

    Returns:
        The closed form (over Sage's symbolic ring, in a variable named as the parameter) and the tactic.

    Raises:
        CertificateError: If `A` is not diagonalizable over ℚ.

    Examples:
        >>> e, proof = diagonalizable_exponential(matrix(QQ, [[0, 1], [1, 0]]), 'φ')
        >>> e[0, 0]
        1/2*e^(-φ) + 1/2*e^φ
    """
    a = matrix(QQ, a)
    try:
        d, p = a.diagonalization()
    except ValueError:
        message = 'the matrix is not diagonalizable over ℚ; use a Jordan decomposition'
        raise CertificateError(message) from None
    t = var(parameter)
    exp_d = diagonal_matrix(SR, [SR(lam * t).exp() for lam in d.diagonal()])
    e = matrix(SR, p) * exp_d * matrix(SR, p.inverse())
    eigen = ', '.join(f'{_rational(lam)} * {parameter}' for lam in d.diagonal())
    p_text, q_text = _literal(p), _literal(p.inverse())
    lines = [
        f'have hPQ : {p_text} * {q_text} = 1 := by',
        '  ext i j; fin_cases i <;> fin_cases j <;> norm_num [Matrix.mul_apply, Fin.sum_univ_succ, Matrix.one_apply]',
        f'have hinv : {p_text}⁻¹ = {q_text} := Matrix.inv_eq_right_inv hPQ',
        f'have hunit : IsUnit {p_text} := ⟨⟨_, _, hPQ, mul_eq_one_comm.mp hPQ⟩, rfl⟩',
        f'have hconj : {parameter} • {_literal(a)} = {p_text} * Matrix.diagonal ![{eigen}] * {p_text}⁻¹ := by',
        '  rw [hinv]',
        f'  ext i j; fin_cases i <;> fin_cases j <;> {ENTRY_SIMP} <;> ring',
        'rw [hconj, Matrix.exp_conj _ _ hunit, Matrix.exp_diagonal, hinv, Pi.exp_def]',
        'ext i j; fin_cases i <;> fin_cases j <;>',
        f'  {ENTRY_SIMP.replace("]", ", ← Real.exp_eq_exp_ℝ, Real.cosh_eq, Real.sinh_eq]")} <;> ring',
    ]
    return e, tactic('\n'.join(lines))
