# name: signature
# technique: an explicit congruence P^T S P = diag(d) by symmetric Gaussian elimination
# goal: Veriphy.Linear.HasSignature S p q z, for an explicit symmetric matrix S over ℚ
# description: Sage finds P and d and counts the signs; Lean checks det P ≠ 0, the congruence and the counts.
MATRIX = None  # EDIT: the symmetric matrix as the goal states it, as [[2, 1], [1, 2]]
assert MATRIX is not None, 'fill in MATRIX in a copy'
s = matrix(QQ, MATRIX)
p, d = symmetric_congruence(s)
print('signature (positive, negative, zero):', signature(d))
proof = tactic(signature_proof(s))
