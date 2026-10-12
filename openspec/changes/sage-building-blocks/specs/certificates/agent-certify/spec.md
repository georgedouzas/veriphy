# Spec Delta

## MODIFIED Requirements

### Requirement: Agent workflow documents the route
The `prove` workflow SHALL direct the agent to build proofs with `sage_run` and the toolkit: inspect the problem, script the search, emit Lean, and iterate on the combined feedback. It SHALL present the presets and `sage_certify` as shortcuts. The agent SHALL report `blocked-missing-building-block`, naming the missing search primitive or emitter, only when the toolkit cannot express the needed proof.

#### Scenario: Missing dedicated tactic, available family
- **WHEN** the agent needs a weighted-square inequality that no preset finds
- **THEN** the documented workflow leads it to a `sage_run` script that uses the product search and the `nlinarith` emitter, not to a report

#### Scenario: Genuine gap
- **WHEN** the proof needs a Sage computation that no toolkit primitive provides
- **THEN** the agent reports `blocked-missing-building-block`, naming that computation
