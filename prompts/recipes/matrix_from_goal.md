# Matrix computation from the goal

## When to use

- The goal states an identity, determinant or trace of explicit matrices or vectors (`!![…]` and `![…]` literals,
  `*`, `+`, `•`, transposes `ᵀ`, `*ᵥ`, `ᵥ*`, `⬝ᵥ`, `det`, `trace`, named matrices whose definition is a literal),
  possibly with symbolic entries.
- Unlike `matrix_identity`, nothing is transcribed by hand. `goal.expr` already holds `lhs - rhs` as a Sage matrix
  (or a scalar for `det` and `trace`), read from the goal itself.
- Sage checks it is zero and reports the actual difference when it is not. Lean proves a matrix or vector identity
  entry by entry (`simp` with `Matrix.mul_apply`, `Matrix.transpose_apply`, then `ring1`), and a determinant or
  trace of any size by expanding it (Laplace expansion along the first row, the trace as a sum).
- **Side relations.** Entries with `cosh` and `sinh`, `cos` and `sin`, or square roots are often equal only modulo
  an identity of the functions (boosts, rotations, eigenvectors with `√2`). Name the identities in `RELATIONS`
  (`Real.cosh_sq_sub_sinh_sq`, `Real.cos_sq_add_sin_sq`, `Real.sin_sq_add_cos_sq`, `Real.sq_sqrt`): Sage reduces each
  entry modulo them, keeping the functions opaque as Lean does, and each entry closes by `linear_combination` of the
  lemmas with the cofactors of a Gröbner lift. `Real.sq_sqrt`'s condition `0 ≤ a` is discharged by `positivity`.

## Template

Copy it to the project's `.veriphy/certificates/matrix_from_goal.sage` (or a more specific name), adapt the lines
marked `EDIT`, keep the header, and run it with `sage_run file "<name>.sage"`.

```sage
# name: matrix_from_goal
# technique: matrix computation read from the goal, checked entrywise, modulo side relations
# goal: an identity, determinant or trace of explicit matrices or vectors, written in the goal (!![…], ![…], *, ᵀ, *ᵥ, det, trace)
# description: Sage evaluates lhs - rhs from the goal itself; Lean proves it entry by entry or by expanding det or trace.
SIMP = []  # EDIT: extra simp lemmas, for example definitions of named matrices
RELATIONS = []  # EDIT: side relations the entries need, as ['Real.cosh_sq_sub_sinh_sq'], ['Real.sq_sqrt']
proof = matrix_from_goal_proof(goal, problem, simp=SIMP, relations=RELATIONS)
```

## Worked examples

```lean
example : !![(2 : ℚ), 1; 1, 1] * !![1, -1; -1, 2] = 1 := by
  sage_run file "matrix_from_goal.sage"

-- a 4 × 4 determinant, by Laplace expansion
example : Matrix.det !![(1 : ℚ), 0, 0, 0; 0, -1, 0, 0; 0, 0, -1, 0; 0, 0, 0, -1] = -1 := by
  sage_run file "matrix_from_goal.sage"

-- a boost preserves the metric (a copy with RELATIONS = ['Real.cosh_sq_sub_sinh_sq'])
open Matrix in
example (u : ℝ) : (!![Real.cosh u, Real.sinh u; Real.sinh u, Real.cosh u])ᵀ * !![(1 : ℝ), 0; 0, -1] *
    !![Real.cosh u, Real.sinh u; Real.sinh u, Real.cosh u] = !![1, 0; 0, -1] := by
  sage_run file "boost_metric.sage"

-- an eigenvector with a square root, inline
open Matrix in
example : !![(2 : ℝ), 1, 0; 1, 2, 1; 0, 1, 2] *ᵥ ![1, Real.sqrt 2, 1] = (2 + Real.sqrt 2) • ![1, Real.sqrt 2, 1] := by
  sage_run "proof = matrix_from_goal_proof(goal, problem, relations=['Real.sq_sqrt'])"
```

`VeriphyTest/SageRun.lean` also proves a general `4 × 4` determinant, a product with a transpose and symbolic
entries, the field-strength invariant `trace (Fᵀ η F η) = 2 (B² - E²)`, and an orthogonal rotation.

## Failure modes

- **"the identity is false: lhs - rhs = …":** the statement is wrong; the difference shows which entries disagree.
  With relations, the difference is computed with the functions' identities applied, so it is a real disagreement.
- **"the entries vanish only by identities of their functions":** the identity holds, but Lean's `ring1` cannot see
  it; name the identities in `RELATIONS`.
- **"an entry is not zero modulo the relations":** the named relations are not enough; add the missing one, or
  rewrite the entries (a double-angle form, say) before the template.
- **"the goal has no symbolic form":** the matrices are named and their definitions are not literals (`σ₁` built
  from other definitions, `γ 0` with a parameter). Use `matrix_identity` and transcribe them, or unfold the names first
  and add their definitions to `SIMP`.
- **An entry stays open after `simp`:** add the lemmas it needs to `SIMP` (for example a named matrix's definition).
