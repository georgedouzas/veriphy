# packs/general-relativity Specification

## Purpose
TBD - created by archiving change domain-packs. Update Purpose after archive.

## Requirements

### Requirement: General-relativity pack
Veriphy SHALL ship a `general-relativity` pack, requiring `physics`, whose step `check-metric` computes a metric's
curvature with EinsteinPy and checks the claimed property: `vacuum` (the Ricci tensor vanishes), `flat` (the Riemann
tensor vanishes) or `R = <expression>`, granting `curvature-checked` (oracle) above `dimensionally-consistent`.

#### Scenario: Schwarzschild and a wrong metric
- **WHEN** `check-metric` claims the Schwarzschild metric is a vacuum solution, and then the metric with 2M/r²
- **THEN** the first is accepted, and the second refused with a nonzero Ricci component and a point

### Requirement: Residuals SymPy cannot simplify
A residual SymPy does not reduce to zero SHALL be evaluated at points: a value away from zero refuses the claim with
the point, and values that all vanish leave it `undecided`, granting nothing.

#### Scenario: A numerical zero
- **WHEN** a residual vanishes at every point tried but does not simplify to zero
- **THEN** the status is `undecided`, and no level is granted
