# Spec Delta

## ADDED Requirements

### Requirement: Replacement reported only after acceptance
`sage_run` SHALL report its `Sage-free replacement` only after the block closed the goal and passed the axiom check. When
the block does not parse or does not close the goal, the tactic SHALL report the combined error and no replacement. A
block that leaves goals open on purpose (a rewrite step, as the existing requirement allows) SHALL declare it
(`leaving_goals`); its open goals then remain for the next tactic, and only undeclared leftovers are refused.

#### Scenario: Failing block
- **WHEN** a script's block for a `3 × 3` product with a transpose fails to close the goal
- **THEN** the messages contain the combined error and no `Sage-free replacement`

#### Scenario: Declared rewrite step
- **WHEN** the `factor_rewrite` template's block, marked as leaving goals, rewrites `lhs` to its factored form
- **THEN** `factored = rhs` remains for the user's next tactic, and the replacement is reported
