# certificates/agent-certify Specification

## Purpose
Lets the proving agent assemble a one-off certificate at proof time. It writes a short Sage script against the normalized problem, and a fixed checker family verifies the result. Certificate shapes no dedicated tactic covers then no longer block the agent, and the kernel stays the only trusted component.

## Requirements

### Requirement: Agent workflow documents the route
The `prove` workflow SHALL direct the agent to create certificates itself with `sage_run`, the toolkit and the procedures: inspect the problem, pick a recipe, adapt its template, run, and iterate on the combined feedback. The agent SHALL report `blocked-missing-building-block`, naming the missing primitive or emitter, only when the toolkit cannot express the proof.

#### Scenario: Missing dedicated tactic, available family
- **WHEN** the agent needs a weighted-square inequality
- **THEN** the documented workflow leads it to the SOS or hint-search recipe and a `sage_run` script, not to a report

#### Scenario: Genuine gap
- **WHEN** the proof needs a Sage computation no toolkit primitive provides
- **THEN** the agent reports `blocked-missing-building-block` naming that computation
