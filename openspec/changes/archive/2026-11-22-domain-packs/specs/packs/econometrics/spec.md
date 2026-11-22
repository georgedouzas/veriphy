## ADDED Requirements

### Requirement: Econometrics pack
Veriphy SHALL ship an `econometrics` pack, requiring `economics`, whose step `check-regression` refits a regression
with linearmodels, by OLS, two-stage least squares for a formula with `[endogenous ~ instruments]`, or `PanelOLS` given
the entity and time columns, with unadjusted, robust or entity-clustered errors, and compares a coefficient with the
claim, granting `recomputed`. Clustered errors without a panel SHALL fail rather than fall back.

#### Scenario: Fixed effects matter
- **WHEN** the example's returns to training are claimed as 0.080
- **THEN** the panel model with firm and year effects agrees, and pooled OLS differs
