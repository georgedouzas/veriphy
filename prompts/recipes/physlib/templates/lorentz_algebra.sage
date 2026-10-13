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
