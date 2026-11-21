# packs/reproduction Specification

## Purpose
Reproduce an empirical analysis as a pack: the published script and data run in a pinned R image, refused when the data's digest differs from the claim's, compared with the published estimate and varied over declared alternatives, granting `reproduced` and `robust` of the reproduction class, never a proof.

## Requirements

### Requirement: Reproduction pack
Veriphy SHALL ship the pack `reproduction`, requiring only `core`, with the `r` tool pinned by container image, the
primitives `r.run` and `r.vary` of class `reproduction`, the steps `reproduce` and `vary`, the levels
`reproduced` and `robust`, the convention aspect `identification`, the workflow `reproduce-analysis` and the
`reproduce` playbook. Using it SHALL need no change to the core.

#### Scenario: Selecting the pack
- **WHEN** a workspace lists `packs: [core, reproduction]`
- **THEN** `config show` lists the `r` tool, the two primitives, the two steps, the two levels and the workflow, and
  no Lean or SageMath entry

### Requirement: Running an analysis
`r.run` SHALL run an analysis script on a data file whose SHA-256 matches the one in its input, with the given seed,
and return the estimate the script reports. A hash mismatch SHALL refuse to start R.

#### Scenario: Wrong data
- **WHEN** the data file's hash differs from the one in the input
- **THEN** R does not start, and the error names both hashes

### Requirement: Reproduce step
`reproduce` SHALL be declared over `r.run` with `compare` against the claimed estimate and a tolerance, and SHALL grant
`reproduced` when the status is `agrees`. Every record SHALL hold both estimates, the seed and the image digest.

#### Scenario: Matching estimate
- **WHEN** the example claim is reproduced with its script and data
- **THEN** the record's status is `agrees`, it grants `reproduced`, and the claim's own level is `reproduced`

#### Scenario: Differing estimate
- **WHEN** the script's estimate is beyond the tolerance
- **THEN** the status is `differs`, no level is granted, and both estimates are recorded

### Requirement: Vary step
`vary` SHALL run each variation declared with the claim and grant `robust` when the estimate keeps its sign and
significance under every variation. The record SHALL list the variations and their estimates.

#### Scenario: A fragile result
- **WHEN** one declared variation flips the estimate's sign
- **THEN** the claim keeps `reproduced`, and the record names the variation

### Requirement: Playbook and skill
The pack SHALL ship a `reproduce` playbook and skill that extract the claim, its data, its script and its assumptions,
run the workflow, and report each claim's level with its trust class.

#### Scenario: Report wording
- **WHEN** the skill reports a reproduced claim
- **THEN** it says `reproduced (reproduction)` and never calls the claim proved or true
