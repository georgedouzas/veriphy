# Spec Delta

## Purpose

Lets the proving agent assemble a one-off certificate at proof time. It writes a short Sage script against the normalized problem, and a fixed checker family verifies the result. Certificate shapes no dedicated tactic covers then no longer block the agent, and the kernel stays the only trusted component.

## ADDED Requirements

### Requirement: Generic certify tactic
The system SHALL provide the tactic `sage_certify <family> "<sage script>"`, where `<family>` is one of `identity`, `inequality` or `witness`. The tactic SHALL check that the current goal's shape suits the family before it contacts the daemon.

#### Scenario: Family does not match the goal
- **WHEN** `sage_certify witness "..."` runs on a goal `x ≤ y`
- **THEN** it fails without calling Sage, with an error saying that `witness` needs an `∃` goal

### Requirement: Problem is pre-bound in the script
The script SHALL run with the extracted problem already in scope:
- the polynomial ring and one generator per atom, named as in the problem;
- the hypotheses as (name, polynomial, relation) records;
- the goal constraint, or the binders for an `∃` goal;
- a Lean rendering of each atom.

The script communicates its answer by assigning `certificate`.

#### Scenario: Script reads the hypotheses
- **WHEN** the context has `h1 : x + y ≤ 1` and the script iterates over the pre-bound hypotheses
- **THEN** it sees an entry named `h1` with polynomial `x0 + x1 - 1` and relation `le`

### Requirement: Family certificate schemas
Each family SHALL accept exactly one certificate schema:
- `identity`: cofactors, a polynomial for each named hypothesis.
- `inequality`: nonnegative rational weights for named hypotheses, plus optional (coefficient, polynomial) square terms.
- `witness`: one rational per binder.

A certificate that violates its schema SHALL be rejected before reconstruction, with the violation named.

#### Scenario: Witness of the wrong length
- **WHEN** the goal has 2 binders and the script assigns `certificate = [1]`
- **THEN** the tactic fails with an arity error that names `witness`

### Requirement: Checked by the family, not trusted
The certificate SHALL be reconstructed with the shared builders and closed by the family's checker. A wrong certificate SHALL make the tactic fail. It SHALL never produce a proof of a different statement.

#### Scenario: Incorrect inequality weights
- **WHEN** the script returns weights whose combination does not imply the goal
- **THEN** `linear_combination` rejects it, and the tactic fails with the checker's message

#### Scenario: Correct one-off certificate
- **WHEN** the goal is `a * b ≤ (a ^ 2 + b ^ 2) / 2` and the script returns the square term `(1/2, a - b)`
- **THEN** the goal closes

### Requirement: Script-free replacement
On success, `sage_certify` SHALL emit the family's plain checker proof as its `Sage-free replacement:`. The replacement SHALL contain neither the script nor `sage_certify`, and it SHALL pass the replay check.

#### Scenario: Committed proof is Sage-free
- **WHEN** `sage_certify inequality "..."` closes a goal
- **THEN** the suggestion is a `linear_combination ...` proof (or the refutation step block), with no Sage script text

### Requirement: Script diagnostics
If the script raises, times out or assigns no `certificate`, the tactic SHALL fail with the daemon's error. The error SHALL include the script's captured stdout, truncated, so the agent can iterate.

#### Scenario: Script raises
- **WHEN** the script raises `ZeroDivisionError`
- **THEN** the tactic error includes `ZeroDivisionError` and any lines the script printed before failing

### Requirement: Agent workflow documents the route
The `prove` workflow SHALL direct the agent to try `sage_certify` with a fitting family before it reports `blocked-missing-tactic`. That report SHALL be reserved for certificates that no checker family can verify.

#### Scenario: Missing dedicated tactic, available family
- **WHEN** the agent needs a weighted-square inequality that no `sage_*` tactic finds
- **THEN** the documented workflow leads it to `sage_certify inequality` rather than to a `blocked-missing-tactic` report
