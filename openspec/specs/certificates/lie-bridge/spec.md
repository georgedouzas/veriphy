# certificates/lie-bridge Specification

## Purpose
Lets scripts use Sage's Lie theory (structure constants, Killing forms, Casimirs, root systems, Cartan matrices) on Lie algebras given by explicit matrices. Every result reaches Lean as a finite identity between explicit matrices or numbers, which Lean checks exactly.

## Requirements

### Requirement: Lie brackets translate
The translation SHALL cover the Lie bracket `⁅A, B⁆` of matrices (as `A*B - B*A`), and of elements of a matrix Lie subalgebra through their underlying matrix. It SHALL also cover matrices indexed by `Fin n` or by sums of `Fin` types (such as `Fin 1 ⊕ Fin 3`), with the index order recorded so that rendering restores the same index type.

#### Scenario: Bracket of explicit matrices
- **WHEN** the goal is `⁅!![0, 1; 0, 0], !![0, 0; 1, 0]⁆ = !![1, 0; 0, -1]` over ℚ
- **THEN** the script sees both sides as Sage matrices, with the bracket evaluated as a commutator

#### Scenario: Sum-indexed matrix
- **WHEN** a hypothesis involves a matrix of type `Matrix (Fin 1 ⊕ Fin 3) (Fin 1 ⊕ Fin 3) ℝ` given entrywise
- **THEN** the script sees a 4×4 Sage matrix, and rendering it back produces a term of the original index type

### Requirement: Structure-constant certificates
The toolkit SHALL compute, for a list of basis matrices, the structure constants `⁅eᵢ, eⱼ⁆ = Σ cᵢⱼₖ eₖ`, the Killing form matrix and the quadratic Casimir. It SHALL emit Lean proofs of each claimed identity as entrywise matrix identities. Sage's results are only proposals: a basis that is not closed under the bracket SHALL be reported with the offending pair.

#### Scenario: Bracket table of 𝔰𝔩₂
- **WHEN** a script is given the matrices `e`, `f`, `h` of 𝔰𝔩₂ over ℚ
- **THEN** it emits proofs of `⁅h, e⁆ = 2 • e`, `⁅h, f⁆ = -2 • f` and `⁅e, f⁆ = h`

#### Scenario: Casimir commutes
- **WHEN** a script computes the Casimir of 𝔰𝔩₂ in its defining representation
- **THEN** it emits proofs that the Casimir matrix commutes with each basis matrix

### Requirement: Root data as checked matrices
The toolkit SHALL provide Sage's Cartan matrices, inverse Cartan matrices, Weyl group orders and positive roots for a Cartan type. Lean SHALL receive them only as statements Lean can check: matrix identities against mathlib's `CartanMatrix` definitions, determinants, and inverse identities.

#### Scenario: E₈ Cartan matrix determinant
- **WHEN** the goal is `CartanMatrix.E₈.det = 1`
- **THEN** a script using the toolkit's root data closes it by an exact computation Lean checks

### Requirement: Lie recipe
The recipe set SHALL include a `lie_structure` recipe covering bracket tables, closure of a basis, Killing forms, Casimirs and Cartan-matrix facts. Its failure modes SHALL include abstract Lie algebras with no matrix realization in the goal, which are out of scope for the bridge.

#### Scenario: Lorentz algebra element
- **WHEN** the goal states that an explicit 4×4 matrix lies in Physlib's `lorentzAlgebra`, with the `physlib` pack active
- **THEN** the template rewrites by the membership criterion (`Aᵀ * η = -η * A`) and closes it entrywise
