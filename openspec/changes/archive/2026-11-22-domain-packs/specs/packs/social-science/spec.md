## MODIFIED Requirements

### Requirement: Social-science pack
Veriphy SHALL ship a `social-science` pack, needing no Lean and no SageMath and requiring `statistics`, with the step
`check-reliability`, which recomputes a scale's Cronbach's alpha with pingouin and compares it with the claim as
evidence, the convention `sampling`, and the workflow `check-study`.

#### Scenario: Selecting the pack
- **WHEN** a workspace lists `packs: [social-science]`
- **THEN** `veriphy config check` passes, the packs are `core`, `statistics` and `social-science`, and no `lean.*` or
  `sage.*` primitive is configured

## REMOVED Requirements

### Requirement: Analysis in Python
**Reason**: The analysis runner belongs to `statistics`, which every empirical pack builds on.
**Migration**: Select `statistics`, or a pack that requires it; the script receives a pandas DataFrame.

### Requirement: Robustness
**Reason**: Moved to `statistics` with the analysis it reruns.
**Migration**: None needed for workspaces selecting `social-science`, which requires `statistics`.

### Requirement: Concepts against a thesaurus
**Reason**: Every field names concepts, so `check-concepts` belongs to the framework pack.
**Migration**: None: every workspace has `check-concepts`.
