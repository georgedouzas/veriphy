# Signatures of quadratic forms

## When to use

- The goal is `Veriphy.Linear.HasSignature S p q z` for an explicit symmetric matrix over `ℚ`: an invertible `P` with
  `Pᵀ * S * P` diagonal, with `p` positive, `q` negative and `z` zero entries.
- Sage finds `P` by symmetric Gaussian elimination; Lean checks `det P ≠ 0`, the congruence entry by entry and the
  counts by kernel evaluation. That the counts do not depend on `P` (Sylvester's law of inertia) is not part of the
  statement, and not certified.

## Template

Copy it to the project's `.veriphy/certificates/signature.sage` (or a more specific name), adapt the lines marked
`EDIT`, keep the header, and run it with `sage_run file "<name>.sage"`.

```sage
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
```

## Worked examples

```lean
example : Veriphy.Linear.HasSignature !![(2 : ℚ), 1, 0; 1, 2, 1; 0, 1, 2] 3 0 0 := by
  sage_run "proof = tactic(signature_proof(matrix(QQ, [[2, 1, 0], [1, 2, 1], [0, 1, 2]])))"

-- the Minkowski metric
example : Veriphy.Linear.HasSignature !![(1 : ℚ), 0, 0, 0; 0, -1, 0, 0; 0, 0, -1, 0; 0, 0, 0, -1] 1 3 0 := by
  sage_run "proof = tactic(signature_proof(matrix(QQ, [[1, 0, 0, 0], [0, -1, 0, 0], [0, 0, -1, 0], [0, 0, 0, -1]])))"
```

## Failure modes

- **The counts fail:** the stated signature is wrong; the template prints the counts Sage finds.
- **"the matrix is not symmetric":** symmetrise the form first.
