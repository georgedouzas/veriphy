# certificates/certified-numerics Specification

## Purpose
Lets scripts prove numerical facts research arguments depend on (bounds on constants, on special-function values, on roots, on eigenvalues) by exact rational certificates. Sage finds the enclosures with interval arithmetic, and Lean checks the certificates without floating point.

## Requirements

### Requirement: Bounds on transcendental values
The toolkit SHALL prove bounds `a < f(c) < b` for covered functions at explicit points. It SHALL use truncated series with explicit remainder bounds (Taylor with Lagrange remainder, alternating series, geometric tails) whose terms are rational. Sage's interval arithmetic chooses the truncation order and the rational endpoints. The proof uses mathlib's bounds where they exist (`Real.pi_gt_d6`, `Real.exp_bound`, `Real.add_one_le_exp`) and the series lemmas otherwise.

#### Scenario: Exponential bound
- **WHEN** the goal is `Real.exp 1 < 2.7183`
- **THEN** the emitted proof closes it using a truncated series with a rational remainder bound

#### Scenario: π to six digits
- **WHEN** the goal is `3.14159 < Real.pi`
- **THEN** the emitted proof uses mathlib's existing bound lemmas when they suffice

### Requirement: Isolated roots and eigenvalues
The toolkit SHALL isolate real roots of explicit polynomials in rational intervals, by Sturm sequences or Descartes bounds checked as sign changes. It SHALL emit proofs that each interval contains exactly one root, by the intermediate value theorem with sign evaluations, and, for counts, the sign sequence certificate. Eigenvalue bounds of explicit symmetric matrices SHALL be certified through their characteristic polynomial.

#### Scenario: Root in an interval
- **WHEN** the goal is `∃ x, 1 < x ∧ x < 2 ∧ x ^ 3 - 2 * x - 1 = 0`
- **THEN** the emitted proof applies the intermediate value theorem with rational sign evaluations

### Requirement: Numerics recipe
The recipe set SHALL include `certified_bound` and `root_isolation`. Their failure modes SHALL include functions with no series lemma in mathlib, and points too close to a singularity for the chosen order.

#### Scenario: Unsupported function
- **WHEN** a bound on `Real.Gamma (1/3)` is requested
- **THEN** the template reports that no remainder bound is available for `Gamma`, rather than emitting an unchecked bound
