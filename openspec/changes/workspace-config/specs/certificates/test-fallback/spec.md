# Spec Delta

## MODIFIED Requirements

### Requirement: Verification levels
Every claim SHALL carry one of five levels, in this order: `certificate`, `lean-proof` and `kernel-test` (trust class
`kernel`), `oracle-test` (class `oracle`) and `none`. `certificate` and `lean-proof` SHALL require the standard axioms
alone. The `math` pack SHALL declare these levels. A claim SHALL get the highest feasible level, and the fallback SHALL
apply only when no recipe applies.

#### Scenario: A recipe exists
- **WHEN** the goal is `Matrix.rank !![(1 : ℚ), 2, 3; 2, 4, 6] = 1` and the `matrix_rank` recipe closes it
- **THEN** the claim's level is `certificate`, and `sage_test` is not used

#### Scenario: No certificate is feasible
- **WHEN** the claim is rank-nullity for an arbitrary `A : Matrix (Fin m) (Fin n) ℚ`
- **THEN** its proof is a mathlib proof, and its Veriphy check is a `sage_test` at level `kernel-test`

#### Scenario: A plain mathlib proof
- **WHEN** a theorem has a complete proof that no recipe built, on the standard axioms
- **THEN** its level is `lean-proof`

#### Scenario: A proof on another axiom
- **WHEN** a theorem carries the recipe marker and depends on `sorry` or on an axiom beyond the standard ones
- **THEN** its level is `none`

#### Scenario: Levels from the pack
- **WHEN** `python -m veriphy config show` runs with the default config
- **THEN** it lists the five levels with their trust classes, matching what `#veriphy_levels` reports
