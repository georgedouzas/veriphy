# name: boost
# technique: closed forms of matrix exponentials, proved against mathlib's NormedSpace.exp
# goal: NormedSpace.exp N = E for nilpotent N, or NormedSpace.exp (t • A) = E for A diagonalizable over ℚ
# description: A nilpotent series stops; otherwise A = P D P⁻¹ and Matrix.exp_conj, Matrix.exp_diagonal give the entries.
MATRIX = matrix(QQ, [[0, 1, 0, 0], [1, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]])
PARAMETER = 'φ'
assert MATRIX is not None, 'fill in MATRIX (and PARAMETER) in a copy'
if nilpotency_index(MATRIX) is not None:
    closed, proof = nilpotent_exponential(MATRIX)
else:
    closed, proof = diagonalizable_exponential(MATRIX, PARAMETER)
print(closed)
