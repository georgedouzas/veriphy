# Spec Delta

## Purpose

Lets scripts prove closed forms of hypergeometric and holonomic sums and recurrences with the classical certificates (Wilf–Zeilberger pairs, Gosper and Zeilberger telescopers, holonomic recurrences). Lean checks each certificate as a rational-function identity plus a telescoping argument.

## ADDED Requirements

### Requirement: WZ and creative-telescoping certificates
For a sum `Σₖ F(n, k) = S(n)` with a hypergeometric summand, the toolkit SHALL search for one of:
- a WZ certificate `R(n, k)`;
- a Zeilberger telescoper and certificate, giving a recurrence in `n` that `S(n)` satisfies;
- a Gosper antidifference, for indefinite sums.

#### Scenario: Binomial sum
- **WHEN** the goal is `∑ k ∈ Finset.range (n + 1), (n.choose k : ℚ) = 2 ^ n`
- **THEN** a WZ certificate is found and the emitted proof closes the goal

#### Scenario: Gosper-summable sum
- **WHEN** the goal is `∑ k ∈ Finset.range n, (k * k.factorial : ℚ) = n.factorial - 1`
- **THEN** a Gosper antidifference is found and the telescoping proof closes the goal

### Requirement: Telescoping proofs
The emitted Lean proof of a summation certificate SHALL:
- state the summand identity, `F(n+1,k) - F(n,k) = G(n,k+1) - G(n,k)` or its recurrence form;
- prove it by `field_simp; ring` under the nonzero conditions of the certificate's denominators;
- sum it with telescoping lemmas;
- conclude by induction on `n` with the base cases.

#### Scenario: Denominator condition
- **WHEN** a WZ certificate has the denominator `n + 1 - k`
- **THEN** the proof discharges `n + 1 - k ≠ 0` on the summation range before using the summand identity

### Requirement: Holonomic recurrences
For a sequence given by a holonomic recurrence, the toolkit SHALL guess and verify closed forms or recurrences (Sage's `guess`, `ore_algebra` when installed). It SHALL emit a proof by induction that the closed form satisfies the recurrence and the initial values.

#### Scenario: Recurrence with a closed form
- **WHEN** the hypotheses define `a (n + 2) = 5 * a (n + 1) - 6 * a n` with `a 0 = 0` and `a 1 = 1`
- **THEN** the closed form `3 ^ n - 2 ^ n` is found and proved by strong induction

### Requirement: Summation recipes
The recipe set SHALL include `wz_certificate` and `recurrence`, and `sum_induction` SHALL point to them when no closed form is guessable by evaluation. When the optional `ore_algebra` package is missing, the failure SHALL name the install command.

#### Scenario: Missing optional package
- **WHEN** a holonomic recurrence search needs `ore_algebra` and it is not installed in Sage
- **THEN** the script fails with `sage -pip install ore_algebra`
