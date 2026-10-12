# Spec Delta

## Purpose

Lets the agent close a goal with whatever proof a Sage script can assemble. The script turns Sage computations into a Lean tactic block, and Lean alone decides whether that block proves the goal.

## ADDED Requirements

### Requirement: General script tactic
The system SHALL provide the tactic `sage_run "<sage script>"`. It extracts the current goal and its usable hypotheses, runs the script in Sage with the problem and the toolkit pre-bound, and reads back the Lean tactic block the script assigns to `proof`. It then runs that block on the goal.

#### Scenario: Hint-driven inequality
- **WHEN** the goal is `0 ≤ a ^ 2 * b ^ 2 - 2 * a * b + 1` and the script assigns `proof = nlinarith_hints([sq_nonneg(x0 * x1 - 1)])`
- **THEN** the goal closes, and the emitted replacement is the `nlinarith [sq_nonneg (a * b - 1)]` call

### Requirement: Problem context for scripts
The script SHALL see, pre-bound:
- the polynomial ring and one generator per atom;
- each atom's Lean text;
- the hypotheses, as name, polynomial, relation and Lean text;
- the goal, as polynomial and relation when it has a polynomial form, and always as Lean text;
- the binders of an existential goal.

Hypotheses that do not translate to polynomials SHALL still appear, with their Lean text.

#### Scenario: Non-polynomial hypothesis is visible
- **WHEN** the context contains `hs : Real.sin x ≤ 1`
- **THEN** the script sees a hypothesis named `hs` with its Lean text and no polynomial form

### Requirement: Only standard axioms
After the block runs, the proof term SHALL be rejected if it depends on `sorryAx` or on any axiom outside `propext`, `Classical.choice` and `Quot.sound`. In that case the tactic fails, the goal is unchanged and nothing is emitted.

#### Scenario: Script emits sorry
- **WHEN** a script assigns `proof = "sorry"`
- **THEN** the tactic fails with an error naming `sorryAx`, and no suggestion is attached

#### Scenario: Script emits native_decide
- **WHEN** a script's block closes the goal with `native_decide`
- **THEN** the tactic fails with an error naming the non-standard axiom it depends on

### Requirement: Sage-free replacement through the shared pipeline
A successful `sage_run` SHALL emit the block, exactly as run, as its one `Sage-free replacement:`. When `veriphy.checkReplay` is on, it SHALL pass the replay check. The replacement SHALL NOT contain the script.

#### Scenario: Replay on
- **WHEN** `sage_run` closes a goal under `set_option veriphy.checkReplay true`
- **THEN** the printed block is re-parsed and re-run with Sage disabled, and leaves the same goals

### Requirement: Combined feedback on failure
When the script fails, assigns no `proof`, or produces a block that does not parse or does not close the goal, the error SHALL include:
- the script's printed output (truncated);
- the produced Lean text, when there is any;
- Lean's parse or elaboration error, with its position inside that text.

#### Scenario: Wrong hint
- **WHEN** the script's block is `nlinarith [sq_nonneg (a - b)]` and `nlinarith` fails
- **THEN** the error shows the script output, the block, and `nlinarith`'s failure message

#### Scenario: Unparseable block
- **WHEN** the script assigns `proof = "linear_combination (h1"`
- **THEN** the error shows the parse error at its position in the block, and the block itself

### Requirement: Residual goals are allowed and reported
A block MAY leave goals open, for example after a rewrite step. Those goals SHALL remain for the user's next tactic, and the replacement SHALL carry the same behavior.

#### Scenario: Rewrite step leaves a goal
- **WHEN** the block rewrites `lhs` to a factored form by `ring` and leaves `factored = rhs`
- **THEN** the goal `factored = rhs` remains after `sage_run`, as it does after the replacement
