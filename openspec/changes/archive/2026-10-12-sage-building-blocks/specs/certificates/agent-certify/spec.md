# Spec Delta

## REMOVED Requirements

### Requirement: Generic certify tactic
**Reason**: `sage_run` subsumes `sage_certify`: a script returns any Lean proof instead of one of three certificate schemas.
**Migration**: Replace `sage_certify <family> "<script>"` with `sage_run`, building the proof with the toolkit's emitters (the procedures show each former family).

### Requirement: Problem is pre-bound in the script
**Reason**: Superseded by the problem context of `certificates/script-tactic`.
**Migration**: Scripts read `problem` (and the same short names) in `sage_run`.

### Requirement: Family certificate schemas
**Reason**: Veriphy no longer ships ready-made certificates; agents and users build each certificate with `sage_run`, the toolkit and the procedures.
**Migration**: Emit the proof directly with the toolkit.

### Requirement: Checked by the family, not trusted
**Reason**: Superseded by `certificates/script-tactic`: Lean checks the emitted proof, and the axiom guard rejects `sorry` and non-standard axioms.
**Migration**: None needed.

### Requirement: Script-free replacement
**Reason**: Superseded by the Sage-free replacement requirement of `certificates/script-tactic`.
**Migration**: None needed.

### Requirement: Script diagnostics
**Reason**: Superseded by the combined feedback requirement of `certificates/script-tactic`.
**Migration**: None needed.

## MODIFIED Requirements

### Requirement: Agent workflow documents the route
The `prove` workflow SHALL direct the agent to create certificates itself with `sage_run`, the toolkit and the procedures: inspect the problem, pick a recipe, adapt its template, run, and iterate on the combined feedback. The agent SHALL report `blocked-missing-building-block`, naming the missing primitive or emitter, only when the toolkit cannot express the proof.

#### Scenario: Missing dedicated tactic, available family
- **WHEN** the agent needs a weighted-square inequality
- **THEN** the documented workflow leads it to the SOS or hint-search recipe and a `sage_run` script, not to a report

#### Scenario: Genuine gap
- **WHEN** the proof needs a Sage computation no toolkit primitive provides
- **THEN** the agent reports `blocked-missing-building-block` naming that computation
