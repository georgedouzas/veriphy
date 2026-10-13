# Spec Delta

## Purpose

Brings the computational side of category theory into reach: fusion rules, F- and R-symbols of fusion and braided fusion categories (anyon models in topological phases), and naturality of explicit linear natural transformations. Each claim becomes a finite algebraic identity Lean checks over a cyclotomic field. Abstract category theory stays with mathlib's own automation (`aesop_cat`, `simp`, coherence), which Veriphy does not duplicate.

## ADDED Requirements

### Requirement: Fusion data from Sage
The toolkit SHALL obtain fusion rules, F-symbols and R-symbols from Sage (`FusionRing`, its F-matrix solver) for a quantum group at a root of unity or a user-supplied table, with exact entries in `CyclotomicField n ℚ` or an explicit quotient `ℚ[x]/Φₙ`. It SHALL emit proofs that the fusion rules are associative and have a unit and duals.

#### Scenario: Fusion rules of SU(2) level 2
- **WHEN** a script requests the fusion ring of SU(2) at level 2
- **THEN** it emits the rules `σ × σ = 1 + ψ`, `σ × ψ = σ`, `ψ × ψ = 1`, with proofs of associativity

### Requirement: Pentagon and hexagon equations checked
The toolkit SHALL emit Lean proofs that the F-symbols satisfy the pentagon equations and the R-symbols satisfy the hexagon equations, using the reflective checkers above the size threshold.

#### Scenario: Fibonacci anyons
- **WHEN** a script requests the Fibonacci fusion category
- **THEN** it emits the F-matrix with entries in `ℚ(√5)` and proofs of every pentagon equation

#### Scenario: Ising braiding
- **WHEN** a script requests the Ising category's R-symbols
- **THEN** it emits proofs of the hexagon equations over `ℚ(ζ₁₆)`

### Requirement: A Lean structure to state fusion data against
Veriphy SHALL ship, as a recipe asset that projects copy into `.veriphy/lean/`, a mathlib-only Lean definition of multiplicity-free fusion data (labels, fusion rules, F-symbols, R-symbols) with the pentagon and hexagon equations as propositions. The bridge targets it until mathlib provides an equivalent.

#### Scenario: Asset builds alone
- **WHEN** a project copies the fusion-data asset
- **THEN** it builds against mathlib with no `sorry`

### Requirement: Naturality of explicit transformations
The toolkit SHALL certify that an explicit family of matrices is a natural transformation between explicit linear functors, given as representation matrices on finitely many objects and morphisms. It checks each naturality square as a matrix identity, and isomorphism by explicit inverses.

#### Scenario: Intertwiner as a natural transformation
- **WHEN** a script is given two representations of a finite group as functors from its one-object category, and a candidate intertwiner
- **THEN** it emits proofs of the naturality square for each generator

### Requirement: Fusion recipe
The recipe set SHALL include `fusion_category`, with failure modes for categories with multiplicities (out of scope for the multiplicity-free asset) and gauge choices that differ from the goal's (fix the gauge in the template).

#### Scenario: Gauge mismatch
- **WHEN** the goal's F-symbols are in a different gauge from Sage's
- **THEN** the template reports the mismatch and the gauge transformation that relates them, which it can then certify
