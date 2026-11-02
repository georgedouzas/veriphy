# Spec Delta

## MODIFIED Requirements

### Requirement: Levels from the environment
Each exported claim SHALL carry the level `#veriphy_levels` reports for it: `certificate`, `lean-proof`, `kernel-test`,
`oracle-test` or `none`. The export SHALL NOT compute a level any other way.

#### Scenario: A recipe-built proof
- **WHEN** the theorem `KK.boost_metric` was proved by a replacement that holds the marker `Veriphy.certified`
- **THEN** its exported level is `certificate`

#### Scenario: A tested claim
- **WHEN** `KK.trace_identity` carries `veriphy_tested kernel_test 3 0`
- **THEN** its exported level is `kernel-test`

#### Scenario: A plain proof
- **WHEN** the theorem `KK.plain` has a complete proof that no recipe built, on the standard axioms
- **THEN** its exported level is `lean-proof`
