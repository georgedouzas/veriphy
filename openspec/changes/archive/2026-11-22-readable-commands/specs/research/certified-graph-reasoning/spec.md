## ADDED Requirements

### Requirement: Levels from records in the reasoning
A level a step's record grants to a claim, by naming it in its inputs, SHALL be asserted in the claim graph before
reasoning, as one `hasLevel` assertion per claim at the highest such level, with the provenance `record`, so that the
checked run and every effective level take it into account.

#### Scenario: A reproduced estimate
- **WHEN** a `reproduce` record names the claim `trust-education`, which rests on no other claim, and grants
  `reproduced`
- **THEN** the claim's own and effective levels are both `reproduced`
