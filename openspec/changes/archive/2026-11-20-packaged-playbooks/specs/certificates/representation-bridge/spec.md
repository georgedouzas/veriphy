# Spec Delta

## MODIFIED Requirements

### Requirement: Representation recipes
The recipe set SHALL include `representation` (explicit representations and decompositions) and `lie_superalgebra`. Their failure modes SHALL include representations too large for entrywise checking (use the reflective checkers), and claims for which mathlib has no statement yet (report `blocked-library-gap` with the needed definition).

#### Scenario: Recipe index
- **WHEN** an agent's goal is a branching statement
- **THEN** the recipe index in the `prove` playbook routes it to `representation`
