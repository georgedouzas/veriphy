# Matrix exponentials

## When to use

- The goal states a closed form of mathlib's `NormedSpace.exp` of an explicit matrix: `exp N = E` for nilpotent `N`,
  or `exp (t • A) = E` for `A` diagonalizable over ℚ (a Lorentz boost, a rotation generator over ℂ excluded).
- Nilpotent: `exp N = Σ_{k<index} Nᵏ / k!`, from `NormedSpace.exp_eq_tsum_rat` and the finite support of the series.
- Diagonalizable: `A = P D P⁻¹`, so `exp (t • A) = P exp (t • D) P⁻¹` (`Matrix.exp_conj`, `Matrix.exp_diagonal`), and
  the entries are compared with the goal's after unfolding `Real.cosh` and `Real.sinh` into exponentials.

## Template

Copy it to the project's `.veriphy/certificates/matrix_exponential.sage` (or a more specific name), adapt the lines marked `EDIT`,
keep the header, and run it with `sage_run file "<name>.sage"`.

```sage
# name: matrix_exponential
# technique: closed forms of matrix exponentials, proved against mathlib's NormedSpace.exp
# goal: NormedSpace.exp N = E for nilpotent N, or NormedSpace.exp (t • A) = E for A diagonalizable over ℚ
# description: A nilpotent series stops; otherwise A = P D P⁻¹ and Matrix.exp_conj, Matrix.exp_diagonal give the entries.
MATRIX = None  # EDIT: the matrix N or A (Sage, rational)
PARAMETER = 't'  # EDIT: the Lean name of the real parameter multiplying A (unused for a nilpotent N)
assert MATRIX is not None, 'fill in MATRIX (and PARAMETER) in a copy'
if nilpotency_index(MATRIX) is not None:
    closed, proof = nilpotent_exponential(MATRIX)
else:
    closed, proof = diagonalizable_exponential(MATRIX, PARAMETER)
print(closed)
```

## Worked examples

```lean
-- with MATRIX = the boost generator along x and PARAMETER = 'φ'
example (φ : ℝ) : NormedSpace.exp (φ • !![(0 : ℝ), 1, 0, 0; 1, 0, 0, 0; 0, 0, 0, 0; 0, 0, 0, 0]) =
    !![Real.cosh φ, Real.sinh φ, 0, 0; Real.sinh φ, Real.cosh φ, 0, 0; 0, 0, 1, 0; 0, 0, 0, 1] := by
  sage_run file "boost.sage"
```

## Failure modes

- **"fill in MATRIX":** copy the template and fill in the matrix.
- **"not diagonalizable over ℚ":** a Jordan block needs `exp (D + N) = exp D * exp N` for commuting `D`, `N`
  (`Matrix.exp_add_of_commute`) and the nilpotent series for `N`; a rotation generator has eigenvalues `±i` and is
  diagonalizable only over ℂ.
- **An entry that `simp; ring` leaves open:** the goal writes the entry in another form (`exp (-φ)` against
  `1 / exp φ`); rewrite the goal's side first.
