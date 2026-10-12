# certificates/checker-families Specification

## Purpose
Defines the fixed set of kernel-checked proof shapes that certificate tactics close goals with, and the uniform contract by which a tactic runs its check and emits a Sage-free replacement.

## Requirements

### Requirement: Uniform close-and-emit
Every family SHALL run its proof against the current goal and, on success, emit exactly one `Try this:` replacement headed `Sage-free replacement:`. On failure the goal SHALL be unchanged and no suggestion SHALL be emitted.

#### Scenario: Successful close
- **WHEN** any `sage_*` tactic closes its goal through a family
- **THEN** exactly one `Sage-free replacement:` suggestion is attached to the tactic's syntax

#### Scenario: Failed check
- **WHEN** the family's checker rejects the built proof
- **THEN** the tactic errors, the goal list is unchanged, and no suggestion is attached
