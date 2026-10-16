# Spec Delta

## ADDED Requirements

### Requirement: matrix_from_goal covers the pilot's shapes
The `matrix_from_goal` template SHALL close determinants of `4 × 4` literals, products involving transposes,
identities with symbolic entries, and traces of products. It does so by Laplace expansion, the
`Matrix.mul_apply`/`Matrix.transpose_apply` simp set, a final `ring1`, and the trace simp set.

#### Scenario: Four by four determinant
- **WHEN** the goal is `Matrix.det !![(1 : ℚ), 0, 0, 0; 0, -1, 0, 0; 0, 0, -1, 0; 0, 0, 0, -1] = -1`
- **THEN** the template closes it

#### Scenario: Trace of a product
- **WHEN** the goal is `Matrix.trace (Fᵀ * η * F * η) = 2 * (B ^ 2 - E ^ 2)` for a `4 × 4` field-strength matrix `F` and
  the Minkowski metric `η` (the invariant `F_μν F^μν`; `Matrix.trace (F * Fᵀ)` is the sum of squares `2 * (B ^ 2 + E ^ 2)`)
- **THEN** the template closes it

### Requirement: Identities modulo side relations
`matrix_from_goal` SHALL accept `relations`, a list of Lean lemmas of the form `lhs = rhs`. Sage SHALL reduce each entry
of the goal's difference modulo the relations, and the proof SHALL close each entry by `linear_combination` of the
lemmas with the cofactors Sage found.

#### Scenario: Lorentz boost
- **WHEN** the goal is `Λᵀ * η * Λ = η` with `cosh u` and `sinh u` entries and `relations=['Real.cosh_sq_sub_sinh_sq']`
- **THEN** the template closes it

#### Scenario: Square-root eigenvector
- **WHEN** the goal is `B * !![1; √2; 1] = (2 + √2) • !![1; √2; 1]` with `relations=['Real.sq_sqrt']`
- **THEN** the template closes it, with the condition `0 ≤ 2` discharged

### Requirement: Trigonometric table entries
The core rewrite table SHALL contain the Pythagorean identity, the power-reduction formulas for `cos²` and `sin²`, and
the double- and triple-angle formulas for `sin` and `cos`, so that `transcendental_rewrite` selects them without project
entries.

#### Scenario: Power reduction
- **WHEN** the goal is `Real.cos x ^ 2 = 1 / 2 + 1 / 2 * Real.cos (2 * x)`
- **THEN** `transcendental_rewrite` closes it with the core table

### Requirement: Definite integral recipe
The recipe set SHALL include `definite_integral`, for goals `∫ x in a..b, f x = v` where Sage finds an elementary
antiderivative. The proof SHALL establish `HasDerivAt` of the antiderivative with the `has_deriv_at` emitter, apply
`intervalIntegral.integral_eq_sub_of_hasDerivAt`, and evaluate the endpoints with the rewrite table and `norm_num`.

#### Scenario: Mean of the squared cosine
- **WHEN** the goal is `∫ φ in (0 : ℝ)..(2 * Real.pi), Real.cos φ ^ 2 = Real.pi`
- **THEN** the template closes it with the antiderivative `φ / 2 + Real.sin (2 * φ) / 4`
