# Spec Delta

## Purpose

Exports the formalized part of a research project from the Lean environment into the claim graph, so its claims,
levels and dependencies come from what the kernel checked and not from extraction.

## ADDED Requirements

### Requirement: The veriphy_graph command
The system SHALL provide the command `#veriphy_graph p₁ … pₙ`, which writes every declaration under the prefixes
to `.veriphy/graph/lean/` with provenance `lean`: theorems and definitions of type `Prop` as claims, other
definitions as definitions. A second run SHALL replace the files of the first.

#### Scenario: Exporting a project
- **WHEN** `#veriphy_graph KK` runs in a module that imports the project
- **THEN** `.veriphy/graph/lean/` holds one node per theorem and definition under `KK`, and the command reports the
  numbers of claims, definitions and dependencies it wrote

#### Scenario: A prefix with no declarations
- **WHEN** `#veriphy_graph Missing` runs and no declaration starts with `Missing`
- **THEN** the command fails and names the prefix

### Requirement: Levels from the environment
Each exported claim SHALL carry the level `#veriphy_levels` reports for it: `certificate`, `kernel-test`,
`oracle-test` or `none`. The export SHALL NOT compute a level any other way.

#### Scenario: A recipe-built proof
- **WHEN** the theorem `KK.boost_metric` was proved by a replacement that holds the marker `Veriphy.certified`
- **THEN** its exported level is `certificate`

#### Scenario: A tested claim
- **WHEN** `KK.trace_identity` carries `veriphy_tested kernel_test 3 0`
- **THEN** its exported level is `kernel-test`

### Requirement: Dependencies from the proof terms
For each exported declaration, the export SHALL write a `uses` triple to every other exported declaration that its
type or its value mentions. A dependency on a declaration outside the prefixes SHALL NOT be written.

#### Scenario: A theorem that uses a lemma
- **WHEN** the proof of `KK.coset_curvature` applies `KK.killing_form_value`
- **THEN** the export holds `KK.coset_curvature uses KK.killing_form_value`

#### Scenario: A mathlib lemma
- **WHEN** the proof of `KK.coset_curvature` applies `Matrix.trace_mul_comm`
- **THEN** the export holds no triple for `Matrix.trace_mul_comm`

### Requirement: Conventions realized in Lean
A convention in a source file SHALL be linked to an exported Lean definition with `realizedBy`. Reasoning SHALL then
derive that every claim which uses the definition, directly or through other claims, assumes the convention. The Lean
export itself SHALL NOT read the source files.

#### Scenario: A metric defined in Lean
- **WHEN** `chapter3.human.ttl` states that the convention `mostly-minus` is realized by the exported definition
  `KK.minkowski`, and the statement of `KK.boost_invariance` mentions `KK.minkowski`
- **THEN** reasoning derives `KK.boost_invariance assumes mostly-minus`, and the derivation cites the exported
  `uses` triple and the `realizedBy` triple
