# certificates/linear-algebra-certificates Specification

## Purpose
Certifies the computational claims of linear algebra over explicit vectors and matrices: dimensions, ranks, linear
independence and spans, failures of linearity, and signatures of quadratic forms.

## Requirements

### Requirement: Dimension recipe
The recipe set SHALL include `dimension`, for goals `Module.finrank K V = n` where `V` is the span of explicit
vectors, the kernel or range of an explicit linear map, a sum or intersection of such subspaces, or a space built
from `Fin n → K`, `Matrix`, `TensorProduct` and `Module.Dual`. Sage SHALL compute the rank, an echelon basis and the
coordinates of the generators.

#### Scenario: Span of two vectors
- **WHEN** the goal is `Module.finrank ℚ ↥(Submodule.span ℚ (Set.range ![![1, 2, 0], ![0, 1, 1]])) = 2`
- **THEN** the template closes it, and the replacement builds without Sage

#### Scenario: Kernel of the trace
- **WHEN** the goal is `Module.finrank ℝ ↥(LinearMap.ker (Matrix.traceLinearMap (Fin 3) ℝ ℝ)) = 8`
- **THEN** the template closes it through rank-nullity with a matrix of trace one as the surjectivity witness

### Requirement: Dimension proofs
The `dimension` emitter SHALL prove a span's dimension by `finrank_span_eq_card` with independence of the basis, a
kernel's by rank-nullity with a surjectivity witness, a sum's or intersection's by `Submodule.finrank_mono` with
`Submodule.eq_of_le_of_finrank_eq`, and a product space's by the product formulas.

#### Scenario: Tensor product
- **WHEN** the goal is `Module.finrank ℝ ((Fin 2 → ℝ) ⊗[ℝ] (Fin 3 → ℝ)) = 6`
- **THEN** the template closes it by the product formula

### Requirement: Matrix rank recipe
The recipe set SHALL include `matrix_rank`, for goals `A.rank = r`, `r ≤ A.rank` and `A.rank ≤ r` with explicit `A`.
Sage SHALL find a non-singular `r × r` minor for the lower bound and a factorisation `A = B * C` with inner size `r`
for the upper bound.

#### Scenario: Rank one
- **WHEN** the goal is `Matrix.rank !![(1 : ℚ), 2, 3; 2, 4, 6] = 1`
- **THEN** the template closes it with the minor `1` and the factorisation `!![1; 2] * !![1, 2, 3]`

### Requirement: Independence and span recipe
The recipe set SHALL include `independence`, for `LinearIndependent K v`, its negation, and equalities of spans with
spans or kernels, for explicit families. Independence SHALL come from a non-zero minor, dependence from an explicit
relation, and span equality from coordinates in both directions.

#### Scenario: Dependent family
- **WHEN** the goal is `¬ LinearIndependent ℚ ![![1, 2], ![2, 4]]`
- **THEN** the template finds the relation `2 v₀ - v₁ = 0` and closes the goal with it

### Requirement: Non-linearity recipe
The recipe set SHALL include `nonlinearity`, for goals `¬ ∃ f : V →ₗ[K] W, ∀ x, f x = g x` and the bilinear analogue.
Sage SHALL find points where additivity, homogeneity or `f 0 = 0` fails, and the proof SHALL specialise `map_add`,
`map_smul` or `map_zero` at them.

#### Scenario: The square is not linear
- **WHEN** the goal is `¬ ∃ f : ℝ →ₗ[ℝ] ℝ, ∀ x, f x = x ^ 2`
- **THEN** the template closes it with `map_smul` at `2` and `1`

### Requirement: Signature recipe
The recipe set SHALL include `signature`, for goals stating that an explicit symmetric matrix is congruent to a
diagonal matrix with given numbers of positive, negative and zero entries. Sage SHALL compute `P` with `Pᵀ S P`
diagonal, and the proof SHALL check the congruence and `det P ≠ 0` with `matrix_from_goal` and the counts with
`norm_num`. The invariance of the counts under the choice of `P` is not certified by this recipe.

#### Scenario: Positive definite form
- **WHEN** the goal states that `!![(2 : ℚ), 1, 0; 1, 2, 1; 0, 1, 2]` has signature `(3, 0, 0)`
- **THEN** the template closes it with an explicit `P` and the diagonal `2, 3/2, 4/3`

### Requirement: Linear packaging lemmas
`Veriphy/Kit/Linear.lean` SHALL provide the lemmas the emitters use, each with the standard axioms only: the span of an
echelon family, rank bounds from a minor and from a factorisation, and independence from a non-zero minor.

#### Scenario: Axiom audit
- **WHEN** `#print axioms` runs on each lemma
- **THEN** it lists only `propext`, `Classical.choice` and `Quot.sound`
