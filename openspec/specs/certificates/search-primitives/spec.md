# certificates/search-primitives Specification

## Purpose
Provides the few exact solvers that are general and hard to get right in a few lines at proof time, so scripts can rely on them. Everything else a certificate needs is ordinary Sage code in the script, shown by the recipes.

## Requirements

### Requirement: Exact results
Every toolkit solver SHALL return exact rationals, never floating-point values. When it finds no solution it SHALL say so with an explicit result or a named error. It SHALL NOT return an approximate answer.

#### Scenario: Infeasible LP
- **WHEN** the exact LP is given `t ≤ 0` and `t ≥ 1`
- **THEN** it returns `None`

### Requirement: Exact linear programming
The toolkit SHALL provide an exact rational LP over equality and inequality rows, with optional nonnegativity and an objective. It SHALL handle problems with no variables or no constraints without failing.

#### Scenario: Empty problem
- **WHEN** the LP has variables but no constraints
- **THEN** it returns the zero point instead of failing in the backend

#### Scenario: Fractional optimum
- **WHEN** the only constraint is `3 t = 1`
- **THEN** it returns `[1/3]` exactly

### Requirement: Exact SOS from a numeric SDP
The toolkit SHALL find a sum-of-squares decomposition `p = Σ cᵢ qᵢ²` with rational `cᵢ ≥ 0`: solve the Gram-matrix SDP numerically, round to rationals, project exactly onto coefficient matching, and verify positive semidefiniteness exactly. If any step fails it SHALL report that no exact SOS was found.

#### Scenario: Irreducible quartic
- **WHEN** the polynomial is an irreducible quartic that is a sum of squares but does not factor
- **THEN** the solver returns rational weights and polynomials whose weighted squares sum exactly to it

#### Scenario: Rounding fails
- **WHEN** the rounded decomposition cannot be made exact
- **THEN** the solver reports failure rather than returning an inexact decomposition
