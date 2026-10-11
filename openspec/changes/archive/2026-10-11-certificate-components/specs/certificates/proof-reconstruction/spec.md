# Spec Delta

## Purpose

Turns untrusted certificate data from Sage into Lean syntax that elaborates now and still parses and elaborates when it is printed and pasted back as a `Try this:` replacement.

## ADDED Requirements

### Requirement: Exact rational literals
Rational strings from a certificate (`"5"`, `"-3/2"`) SHALL become exact Lean literals: an integer numeral, a numeral quotient, or the negation of either. A malformed rational SHALL raise an error that quotes the offending string.

#### Scenario: Negative fraction
- **WHEN** the certificate value is `"-3/2"`
- **THEN** the built term is `-(3 / 2)`

#### Scenario: Malformed rational
- **WHEN** the certificate value is `"1.5"`
- **THEN** reconstruction fails with an error containing `1.5`

### Requirement: Polynomial reconstruction over atoms
A term-list polynomial SHALL become a sum of monomials over the delaborated atoms. Zero exponents are omitted, unit coefficients are omitted, and the empty polynomial becomes `0`.

#### Scenario: Monomial with unit coefficient
- **WHEN** the term is coefficient `1` with exponents `[2, 0, 1]` over atoms `x, y, z`
- **THEN** the built term is `x ^ 2 * z`

#### Scenario: Empty polynomial
- **WHEN** the term list is empty
- **THEN** the built term is `0`

### Requirement: Weighted hypothesis sums
A list of (weight, hypothesis name) pairs SHALL become the sum `w₁ * h₁ + … + wₖ * hₖ`. Zero weights are dropped. If every weight is zero, the builder SHALL raise an "empty certificate" error rather than emit `0`.

#### Scenario: Zero weights are dropped
- **WHEN** the weights are `[0, 2, 1/3]` for hypotheses `[h1, h2, h3]`
- **THEN** the built term mentions `h2` and `h3` only

#### Scenario: All-zero certificate
- **WHEN** every weight is zero
- **THEN** the builder fails with an error stating that the certificate is empty

### Requirement: Witness tuples
A list of rational values for `n` binders SHALL become an anonymous-constructor witness `⟨v₁, …, vₙ, proof⟩`. A value count that differs from the binder count SHALL be an error.

#### Scenario: Witness arity mismatch
- **WHEN** the goal has 2 binders and the certificate supplies 3 values
- **THEN** reconstruction fails with an arity error before any proof is attempted

### Requirement: Step sequences
A sequence of tactic steps SHALL be combinable into one tactic block that runs the steps in order. The same block SHALL be the one that is printed.

#### Scenario: Negate then refute
- **WHEN** a proof consists of a `by_contra` step, a `simp only` step and a `linear_combination` step
- **THEN** the printed replacement is a single block that contains the three steps in that order

### Requirement: Re-parseable identifiers
Every identifier a builder introduces SHALL be unhygienic: fresh local names, lemma names and hypothesis references. Printed output SHALL NOT contain `✝` or macro-scope suffixes. Lemma references SHALL print in a form that resolves under the user's `open` declarations or is fully qualified.

#### Scenario: Fresh name introduced by a refutation step
- **WHEN** a proof introduces the local hypothesis used to negate the goal
- **THEN** the printed replacement names it with a plain identifier and refers to it by the same identifier

#### Scenario: Lemma name in a simp set
- **WHEN** a step uses `not_le` in a `simp only` set
- **THEN** the printed text contains `not_le` without a hygiene marker, and the text re-parses
