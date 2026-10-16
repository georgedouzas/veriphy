# Spec Delta

## ADDED Requirements

### Requirement: Replacement reported only after acceptance
`sage_run` SHALL report its `Sage-free replacement` only after the block closed the goal and passed the axiom check. When
the block does not parse or does not close the goal, the tactic SHALL report the combined error and no replacement.

#### Scenario: Failing block
- **WHEN** a script's block for a `3 × 3` product with a transpose fails to close the goal
- **THEN** the messages contain the combined error and no `Sage-free replacement`
