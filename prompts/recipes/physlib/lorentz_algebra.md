# Lorentz algebra membership (Physlib)

Applies when the `physlib` pack is active (Physlib is imported; `#veriphy_tables` lists `physlib`).

## When to use

- The goal states that an explicit matrix lies in Physlib's `lorentzAlgebra`, the Lie subalgebra of
  `Matrix (Fin 1 ⊕ Fin 3) (Fin 1 ⊕ Fin 3) ℝ` of `A` with `Aᵀ * η = -η * A`.
- The matrix is written by blocks, `Matrix.fromBlocks a b c d`, with the time block first; the pack records the
  metric signature `+---` (`minkowskiMatrix = diag(1, -1, -1, -1)`).
- Sage checks the criterion first when `A` is filled in; Lean then rewrites by `lorentzAlgebra.mem_iff` and
  `minkowskiMatrix.as_block`, multiplies the blocks, and closes each block entrywise.

## Template

Copy it to the project's `.veriphy/certificates/lorentz_algebra.sage`, adapt the lines marked `EDIT`, keep the
header, and run it with `sage_run file "<name>.sage"`.

```sage
# name: lorentz_algebra
# technique: membership in Physlib's lorentzAlgebra by its criterion Aᵀ η = -η A, checked block by block
# goal: Matrix.fromBlocks A B C D ∈ lorentzAlgebra, with explicit blocks (Fin 1 ⊕ Fin 3 indices)
# description: Sage checks the criterion in the pack's metric convention; Lean rewrites by lorentzAlgebra.mem_iff.
A = None  # EDIT: the matrix in Sage (4 by 4, time first), to check the criterion before Lean does
conventions = {key: value for table in problem.tables for key, value in table.conventions}
assert conventions.get('metric_signature') == '+---', 'the physlib pack is not active: import Physlib'
if A is not None:
    eta = diagonal_matrix(QQ, [1, -1, -1, -1])
    defect = A.transpose() * eta + eta * A
    assert defect == 0, f'not in the Lorentz algebra: Aᵀη + ηA =\n{defect}'
proof = tactic(
    'rw [lorentzAlgebra.mem_iff, minkowskiMatrix.as_block]\n'
    'rw [Matrix.fromBlocks_transpose, Matrix.fromBlocks_multiply, Matrix.fromBlocks_neg, Matrix.fromBlocks_multiply]\n'
    'congr 1 <;> ext i j <;> fin_cases i <;> fin_cases j <;> simp'
)
```

## Worked example

```lean
-- the boost generator along x
example : Matrix.fromBlocks !![(0 : ℝ)] !![1, 0, 0] !![1; 0; 0] (0 : Matrix (Fin 3) (Fin 3) ℝ) ∈ lorentzAlgebra := by
  sage_run file "lorentz_algebra.sage"
-- replacement:
--   rw [lorentzAlgebra.mem_iff, minkowskiMatrix.as_block]
--   rw [Matrix.fromBlocks_transpose, Matrix.fromBlocks_multiply, Matrix.fromBlocks_neg, Matrix.fromBlocks_multiply]
--   congr 1 <;> ext i j <;> fin_cases i <;> fin_cases j <;> simp
```

## Failure modes

- **"not in the Lorentz algebra: Aᵀη + ηA = …":** the matrix fails the criterion; the message shows the defect.
  A boost is symmetric between the time and space blocks (`b = cᵀ`), a rotation antisymmetric in the space block.
- **An unsolved goal such as `1 = -1` in a block:** the same failure found by Lean, block by block, when `A` was
  left out of the Sage check.
- **"the physlib pack is not active":** Physlib is not imported in the file.
- **A matrix written as `!![…]` over `Fin 4`:** it has the wrong index type for `lorentzAlgebra`; write it with
  `Matrix.fromBlocks`, or reindex it by `finSumFinEquiv`.
