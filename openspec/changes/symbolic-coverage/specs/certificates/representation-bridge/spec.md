# Spec Delta

## Purpose

Lets scripts use Sage's representation theory (weights, characters, tensor product decompositions, branching rules, Clebsch–Gordan coefficients) and Lie superalgebra computations. Every claim reaches Lean as explicit matrices (representation matrices, intertwiners, projectors) whose defining identities Lean checks.

## ADDED Requirements

### Requirement: Explicit representations
The toolkit SHALL build, from a Cartan type or a matrix Lie algebra and a highest weight, explicit representation matrices for a basis of the algebra, with exact entries over ℚ or a cyclotomic field. It SHALL emit proofs that the matrices satisfy the algebra's bracket relations, so that they define a representation.

#### Scenario: Adjoint of 𝔰𝔩₃
- **WHEN** a script requests the adjoint representation of 𝔰𝔩₃
- **THEN** it obtains eight 8×8 matrices, and emits proofs of every bracket relation

### Requirement: Decompositions certified by intertwiners
A tensor product decomposition or branching rule claimed by Sage SHALL be certified by explicit matrices:
- an invertible change of basis, with its inverse;
- block-diagonal forms of the representation matrices;
- or projectors onto the claimed summands, with their idempotence, orthogonality, completeness and commutation with the algebra.

Dimension or character counts alone SHALL NOT be offered as proofs.

#### Scenario: Two spins
- **WHEN** a script decomposes the tensor product of two spin-½ representations of 𝔰𝔲(2)
- **THEN** it emits projectors onto the spin-0 and spin-1 parts, with proofs that they commute with the generators and sum to the identity

#### Scenario: GUT branching
- **WHEN** a script branches the 10 of SU(5) to SU(3)×SU(2)×U(1) through explicit embedding matrices
- **THEN** it emits the change of basis and the block forms that exhibit the summands `(3̄,1)`, `(3,2)` and `(1,1)`, with each identity proved

### Requirement: Clebsch–Gordan coefficients
The toolkit SHALL compute Clebsch–Gordan coefficients (exact, with square roots kept symbolic or as a cyclotomic or quadratic field). It SHALL emit a proof that the resulting change of basis intertwines the representations.

#### Scenario: Coefficients for 1 ⊗ ½
- **WHEN** a script computes the coefficients for coupling spin 1 with spin ½
- **THEN** the emitted matrix is proved to intertwine the total angular momentum operators

### Requirement: Lie superalgebras
The toolkit SHALL handle ℤ/2-graded matrix Lie superalgebras (including the families `sl(m|n)`, `osp(m|2n)`, `D(2,1;α)`, `G(3)` and `F(4)`) through explicit supermatrices. It SHALL provide:
- the graded bracket;
- the super-Jacobi identity;
- the supertrace;
- the invariant bilinear form and Casimir.

Each is proved as an explicit identity, with the reflective checkers above the size threshold.

#### Scenario: Super-Jacobi for D(2,1;α)
- **WHEN** a script builds `D(2,1;α)` with symbolic `α` in its defining representation
- **THEN** it emits proofs of the super-Jacobi identity on the basis, as identities over `ℚ(α)`

### Requirement: Representation recipes
The recipe set SHALL include `representation` (explicit representations and decompositions) and `lie_superalgebra`. Their failure modes SHALL include representations too large for entrywise checking (use the reflective checkers), and claims for which mathlib has no statement yet (report `blocked-library-gap` with the needed definition).

#### Scenario: Recipe index
- **WHEN** an agent's goal is a branching statement
- **THEN** the recipe index in `prompts/prove.md` routes it to `representation`
