# Spec Delta

## Purpose

Lets scripts write Lean proofs over the full symbolic structure Sage computes with: rational functions, transcendental expressions and matrices. Scripts get denominator- and domain-aware tactic calls, so Lean can check the result.

## ADDED Requirements

### Requirement: Render symbolic expressions
The toolkit SHALL render Sage symbolic-ring expressions, rational functions and matrices as Lean terms over the problem's atoms, through an explicit function table:
- `sqrt`, `exp`, `log`, `sin`, `cos`, `tan` → their `Real` versions (`Complex` for ℂ);
- `pi` → `Real.pi`, `I` → `Complex.I`;
- `abs` → `|·|`;
- matrices → `!![…]` literals.

An unmapped function SHALL be rejected with an error naming it.

#### Scenario: Absolute value of a real
- **WHEN** a script renders `abs(x0 - 1)` with `x0` a real atom
- **THEN** the text is `|x - 1|`, never `Int.natAbs`

#### Scenario: Complex exponential
- **WHEN** a script renders `exp(x0)` with `x0` a complex atom
- **THEN** the text is `Complex.exp z`

#### Scenario: Unmapped function
- **WHEN** a script renders `gamma(x0)`
- **THEN** the toolkit raises an error naming `gamma`

### Requirement: Domain-aware tactic builders
The toolkit SHALL build `field_simp` and `positivity`-based steps that pass the problem's discharged domain conditions as facts. It SHALL refuse to build a step whose required conditions are undischarged, naming them, unless the caller supplies a proof step for each.

#### Scenario: Clearing denominators
- **WHEN** a script clears denominators in a goal with `1 / y`, and `hy : y ≠ 0` discharges the condition
- **THEN** the step is `field_simp [hy]`, or an equivalent that passes `hy`

#### Scenario: Missing condition
- **WHEN** the required condition `0 < x` for `Real.log x` is undischarged
- **THEN** the builder fails with an error naming `0 < x`, unless a proof step for it is supplied

### Requirement: Rewrite chains with named lemmas
The toolkit SHALL build rewrite and `calc` steps justified by named mathlib lemmas (for example `Real.exp_add`, `Real.sqrt_mul_self`), passing the lemma's side conditions from the domain conditions.

#### Scenario: Exponential identity
- **WHEN** a script proves `Real.exp a * Real.exp b = Real.exp (a + b)` with a rewrite by `Real.exp_add`
- **THEN** the emitted step is `rw [← Real.exp_add]` (or equivalent), and it closes the goal
