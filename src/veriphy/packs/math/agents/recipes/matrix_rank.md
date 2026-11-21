# Matrix rank

## When to use

- The goal is `Matrix.rank A = r`, `r ≤ Matrix.rank A` or `Matrix.rank A ≤ r` for an explicit matrix over a field.
- The lower bound comes from a non-singular `r × r` minor (`Veriphy.Linear.le_rank_of_minor`), the upper bound from
  the height or width, or from a factorisation `A = B * C` with inner size `r`, read off the reduced echelon form
  (`Veriphy.Linear.rank_le_of_factor`). Lean checks the minor's determinant and the product by evaluation.

## Template

Copy it to the project's `.veriphy/certificates/matrix_rank.sage` (or a more specific name), adapt the lines marked
`EDIT`, keep the header, and run it with `sage_run file "<name>.sage"`.

```sage
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
```

## Worked examples

```lean
-- rank one: the minor 1 and the factorisation !![1; 2] * !![1, 2, 3]
example : Matrix.rank !![(1 : ℚ), 2, 3; 2, 4, 6] = 1 := by
  sage_run "proof = tactic(rank_proof(matrix(QQ, [[1, 2, 3], [2, 4, 6]])))"
```

## Failure modes

- **"every r × r minor is singular":** the stated rank is too large; the message gives Sage's rank.
- **The upper bound fails:** the stated rank is too small; `print` shows the rank Sage computes.
