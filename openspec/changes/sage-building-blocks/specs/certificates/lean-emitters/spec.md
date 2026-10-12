# Spec Delta

## Purpose

Gives scripts a Python vocabulary for writing Lean proof text from Sage objects. Proofs are composed from parts that are well-formed by construction and printable as committed code, instead of formatted by hand.

## ADDED Requirements

### Requirement: Terms over the goal's atoms
The toolkit SHALL render Sage rationals and polynomials in the problem's ring as Lean terms over the atoms' Lean text. Rationals SHALL be exact numeral quotients, and every compound atom SHALL be parenthesized.

#### Scenario: Polynomial over compound atoms
- **WHEN** a script renders `2*x0^2 - x0*x1/3`, where atom 0 is `f a` and atom 1 is `b`
- **THEN** the text is `2 * (f a) ^ 2 - 1 / 3 * ((f a) * b)` or an equivalent rendering that Lean parses to the same term

### Requirement: Hypothesis references
The toolkit SHALL render a reference to a named hypothesis exactly as the user can write it. It SHALL reject names the problem does not contain.

#### Scenario: Unknown hypothesis
- **WHEN** a script references hypothesis `h9`, which is not in the problem
- **THEN** the toolkit raises an error naming `h9` and listing the known hypotheses

### Requirement: Proof-step builders
The toolkit SHALL provide builders for:
- `linear_combination` sums;
- `sq_nonneg` and `mul_pos`/`mul_nonneg` terms;
- `nlinarith`, `positivity`, `field_simp` and `norm_num` calls with hint or simp lists;
- `rw [show a = b by tac]` steps;
- `calc` chains;
- `by_cases`/`rcases` splits with one block per branch;
- anonymous-constructor witnesses with a side-goal tactic;
- sequences of steps.

Each builder SHALL return Lean text that parses as a tactic or term of the documented category.

#### Scenario: Calc chain
- **WHEN** a script builds a `calc` chain from `lhs` through two intermediate expressions to `rhs`, each step justified by `ring`
- **THEN** the result is one `calc` block with three steps, and Lean parses it

#### Scenario: Case split
- **WHEN** a script builds `by_cases h : x ≤ 0` with one block per branch
- **THEN** the result parses as a single tactic whose two branches carry the given blocks

### Requirement: Unhygienic, re-parseable output
All emitted names SHALL be plain identifiers: fresh hypothesis names, lemma references and binder names. Emitted text SHALL contain no `✝` and no macro scopes, so it re-parses when committed.

#### Scenario: Fresh name collision
- **WHEN** a builder introduces a hypothesis named `h` while the problem already has an `h`
- **THEN** the emitted name is unused in the problem (for example `h_1`), and every reference uses that name

### Requirement: Documented, runnable examples
Every public emitter SHALL carry a doctest example that runs under the test suite.

#### Scenario: Doctests run
- **WHEN** `nox -s tests` runs
- **THEN** each public emitter's example executes and passes
