# Spec Delta

## MODIFIED Requirements

### Requirement: Verification levels
Every claim SHALL carry one of five levels, in this order: `certificate` (a recipe built a kernel-checked proof),
`lean-proof` (a complete Lean proof no recipe built), `kernel-test` (the kernel checked instances by computation),
`oracle-test` (Sage evaluated instances exactly or by intervals) and `none`. `certificate` and `lean-proof` SHALL
require the standard axioms alone. A claim SHALL get the highest feasible level, and the fallback SHALL apply only when
no recipe applies.

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

### Requirement: Level report
`#veriphy_levels [prefixes]` SHALL list the declarations under the prefixes with their level: `kernel-test` or
`oracle-test` for those carrying `veriphy_tested`, `certificate` for theorems on the standard axioms whose proof came
from a recipe's replacement, `lean-proof` for the other theorems on the standard axioms, and `none` otherwise.

#### Scenario: Mixed module
- **WHEN** a module has one certified theorem, one tested theorem, one plain mathlib proof and one theorem using `sorry`
- **THEN** the report lists the levels `certificate`, `kernel-test`, `lean-proof` and `none`
