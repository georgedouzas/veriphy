# name: matrix_rank
# technique: rank bounds from a non-singular minor (below) and a factorisation A = B * C (above)
# goal: Matrix.rank A = r, r ≤ Matrix.rank A or Matrix.rank A ≤ r, for an explicit matrix A over a field
# description: Sage computes the rank, a minor and a rank factorisation; Lean checks the minor's determinant and the product.
MATRIX = None  # EDIT: the matrix as the goal states it, as [[1, 2, 3], [2, 4, 6]]
assert MATRIX is not None, 'fill in MATRIX in a copy'
a = matrix(QQ, MATRIX)
text = goal.text
if '≤' in text:
    kind = 'le' if 'rank' in text.split('≤')[0] else 'ge'
else:
    kind = 'eq'
print('rank:', a.rank())
proof = tactic(rank_proof(a, kind))
