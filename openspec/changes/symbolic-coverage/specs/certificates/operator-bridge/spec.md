# Spec Delta

## Purpose

Lets scripts compute commutators and normal-ordered forms of matrix operators and of differential operators in Sage, and prove the resulting identities in Lean, either entrywise or by applying both sides to an arbitrary test function.

## ADDED Requirements

### Requirement: Partial derivatives translate
The translation SHALL cover partial derivatives in coordinates: `deriv` of a function along one coordinate, written with `Function.update` or with a notation mapped by a library pack or project entry (such as Physlib's `∂[i]`, in the `physlib` pack). Each becomes Sage's `diff` in that coordinate, with the same domain conditions as `deriv`.

#### Scenario: Partial derivative in a coordinate
- **WHEN** the goal contains `deriv (fun t => f (Function.update x 0 t)) (x 0)` for an explicit `f`
- **THEN** the script sees Sage's derivative of `f` in its first coordinate

### Requirement: Differential-operator commutators
The toolkit SHALL apply operators built from multiplication by expressions and partial derivatives to a symbolic test function `ψ`, compute commutators and compositions in Sage, and emit a Lean proof of the resulting operator identity. The proof applies both sides to an arbitrary `ψ` and point, expands them with derivative lemmas, and closes them by `ring_nf`. The test function's differentiability SHALL be a hypothesis passed to the derivative lemmas.

#### Scenario: Canonical commutator
- **WHEN** a script computes `[d/dx, x]` applied to a differentiable `ψ`
- **THEN** it emits a proof that `deriv (fun y => y * ψ y) x - x * deriv ψ x = ψ x`

#### Scenario: Angular momentum
- **WHEN** a script computes `[L₁, L₂]` with `Lᵢ` given in coordinates as `x_j ∂_k - x_k ∂_j`
- **THEN** it emits a proof that the commutator applied to `ψ` equals `L₃` applied to `ψ` (up to the sign convention in the goal), under `ContDiff ℝ 2 ψ`

### Requirement: Matrix-operator identities
The toolkit SHALL compute normal-ordered forms and commutators of words in finitely many explicit matrices (ladder operators truncated to finite dimension, spin matrices, gamma matrices), and emit entrywise proofs of the claimed identities.

#### Scenario: Spin commutator
- **WHEN** a script is given the Pauli matrices
- **THEN** it emits proofs of `σ₁ * σ₂ - σ₂ * σ₁ = 2 * Complex.I • σ₃` and its cyclic versions

### Requirement: Operator recipe
The recipe set SHALL include an `operator_identity` recipe for matrix and differential-operator identities. For library-defined operators, the template SHALL take the operator's unfolding lemmas from the library's pack (for example the `physlib` pack's entries for the ladder operators on Schwartz space) or from a `SIMP` list, and its failure modes SHALL say that operators without such lemmas need them first.

#### Scenario: Library operator with unfolding lemmas
- **WHEN** the goal is a commutator of Physlib's `loweringCLM` and `raisingCLM`, and the `physlib` pack is active
- **THEN** the template reduces the goal to a derivative identity on a test function, and closes it or reports the residual goal

### Requirement: Clifford algebra and gamma-matrix identities
The toolkit SHALL compute, for explicit gamma matrices in a chosen representation and signature:
- traces of products of gamma matrices (with `γ⁵`);
- contraction identities (`γ^μ γ_μ = d`, `γ^μ γ^ν γ_μ = (2 - d) γ^ν`);
- Fierz rearrangement coefficients.

It SHALL emit entrywise or reflective proofs over ℤ[i], and SHALL check the Clifford relation `{γ^μ, γ^ν} = 2 η^{μν}` first. With the `physlib` pack active, the identities SHALL be stated against Physlib's gamma matrices and metric.

#### Scenario: Trace of four gamma matrices
- **WHEN** a script computes `tr(γ^μ γ^ν γ^ρ γ^σ)` in the Dirac representation
- **THEN** it emits proofs of `4 (η^{μν} η^{ρσ} - η^{μρ} η^{νσ} + η^{μσ} η^{νρ})` for every index combination, by the reflective checker

#### Scenario: Fierz identity
- **WHEN** a script requests the Fierz coefficients for the scalar–pseudoscalar–vector–axial–tensor basis
- **THEN** it emits the 5×5 coefficient matrix and a proof of the rearrangement identity entrywise
