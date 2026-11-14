# Matrix identity

## When to use

- An identity between explicit matrices: Clifford relations, representation identities, anticommutators.
- Sage checks it exactly first, and Lean proves it entry by entry.

## Template

Copy it to the project's `.veriphy/certificates/matrix_identity.sage` (or a more specific name), adapt the lines marked `EDIT`, keep the header, and run it with `sage_run file "<name>.sage"`.

```sage
# name: matrix_identity
# technique: matrix identity, checked entrywise
# goal: an identity between explicit matrices (sums, products, transposes)
# description: Check the identity exactly in Sage first; Lean then proves it entry by entry.
A = matrix(QQ, [[0, 1], [1, 0]])   # EDIT: the matrices of the goal
B = matrix(QQ, [[1, 0], [0, -1]])
assert A * B + B * A == 0, 'the identity is false'   # EDIT: the identity
proof = tactic('ext i j\nfin_cases i <;> fin_cases j <;> simp')  # entrywise; add simp lemmas if needed
```

## Worked example

```lean
example : !![(0 : ℚ), 1; 1, 0] * !![1, 0; 0, -1] + !![1, 0; 0, -1] * !![(0 : ℚ), 1; 1, 0] = 0 := by
  sage_run file "matrix_identity.sage"
```

## Failure modes

- **"the identity is false":** fix the statement. This is a `statement-suspect` report if it came from the source.
- **`simp` leaves goals:** add `Matrix.mul_apply, Fin.sum_univ_succ` to the simp set, or use `decide` for small integer matrices.
- **Symbolic entries:** after `ext`, close each entry with `ring`.
