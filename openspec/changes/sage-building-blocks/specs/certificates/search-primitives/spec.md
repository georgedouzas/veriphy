# Spec Delta

## Purpose

Packages SageMath's exact search power as small, composable functions whose results feed the emitters. Scripts get the hard-to-find data a Lean checker needs without reimplementing it.

## ADDED Requirements

### Requirement: Exact results
Every search primitive SHALL return exact data (rationals, polynomials over QQ, rational matrices), never floating-point values. A primitive that finds nothing SHALL say so with a named error, or with an explicit "not found" value as documented. It SHALL NOT return an approximate answer.

#### Scenario: No certificate
- **WHEN** the Farkas search runs on a consistent linear system
- **THEN** it raises the toolkit's named "no certificate" error

### Requirement: Algebraic primitives
The toolkit SHALL provide an exact LP (with guards for empty problems), ideal-membership cofactors (Gröbner `lift`), factorization over QQ, normal forms and substitutions, and a Farkas search for linear systems.

#### Scenario: Cofactors
- **WHEN** a script asks for cofactors of `a^2 + b^2 - 5` over the hypotheses `a + b - 3` and `a*b - 2`
- **THEN** it receives polynomial cofactors whose weighted sum equals the target exactly

### Requirement: Positivity primitives
The toolkit SHALL provide a search for `nlinarith` hint products (degree-2 products of hypotheses and squares that make a linear certificate exist) and SOS decomposition. SOS SHALL work factor-based, from hinted squares, or from a numeric SDP rounded to rationals and then verified exactly.

#### Scenario: nlinarith product search
- **WHEN** the goal is `a * b ≤ (a ^ 2 + b ^ 2) / 2` with no hypotheses
- **THEN** the product search returns a hint list containing a square equivalent to `(a - b) ^ 2`

#### Scenario: Rounded SOS is verified
- **WHEN** the numeric SDP route returns a rounded decomposition that does not exactly equal the polynomial
- **THEN** the primitive reports failure rather than returning the inexact decomposition

### Requirement: Witness and structure primitives
The toolkit SHALL provide:
- rational roots and rational points of equation systems;
- real-root isolation with rational separating points;
- enumeration of sign and case conditions;
- matrix decompositions (inverse, kernel basis, eigenvectors, similarity transforms) whose correctness is a product identity.

#### Scenario: Case split points
- **WHEN** a script isolates the real roots of `x^2 - 2`
- **THEN** it receives rational intervals, one around each root, together with rational points separating them

### Requirement: Results compose with emitters
Each primitive's result SHALL be directly accepted by the matching emitter. LP multipliers go to `linear_combination` sums, product lists to `nlinarith` hints, and decompositions to `calc` or `rw` steps.

#### Scenario: Farkas to Lean
- **WHEN** a script passes the Farkas search result to the refutation emitter
- **THEN** the emitted block closes the `False` goal without further conversion
