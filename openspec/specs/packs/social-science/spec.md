# packs/social-science Specification

## Purpose
TBD - created by archiving change field-packs. Update Purpose after archive.

## Requirements

### Requirement: Social-science pack
Veriphy SHALL ship a `social-science` pack, needing no Lean and no SageMath and requiring `statistics`, with the step
`check-reliability`, which recomputes a scale's Cronbach's alpha with pingouin and compares it with the claim as
evidence, the convention `sampling`, and the workflow `check-study`.

#### Scenario: Selecting the pack
- **WHEN** a workspace lists `packs: [social-science]`
- **THEN** `veriphy config check` passes, the packs are `core`, `statistics` and `social-science`, and no `lean.*` or
  `sage.*` primitive is configured

### Requirement: Measures as conventions
How a construct is measured SHALL be a convention of one aspect per construct, so that a claim resting on two measures
of one construct is a clash once their exclusion is confirmed.

#### Scenario: Two measures of social trust
- **WHEN** the example's policy claim uses two claims that measure social trust differently
- **THEN** `veriphy layers claims clashes` reports the policy claim
