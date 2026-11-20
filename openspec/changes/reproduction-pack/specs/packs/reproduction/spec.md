# Spec Delta

## ADDED Requirements

### Requirement: Reproduction pack
Veriphy SHALL ship the pack `reproduction`, declaring an `r` tool of class `reproduction` pinned by container image,
the levels `reproduced` (above `none`) and `robust` (above `reproduced`), the convention aspect `identification`, and
the workflow `reproduce-analysis`. Using it SHALL need no change to the core.

#### Scenario: Selecting the pack
- **WHEN** a workspace lists `packs: [core, reproduction]`
- **THEN** `config show` lists the `r` tool, the two levels and the workflow, and no SageMath

### Requirement: Reproduce step
`reproduce` SHALL run the claim's analysis script on data whose SHA-256 matches the claim, with a recorded seed, and
compare the reported estimate with the claimed one within the declared tolerance. A match SHALL grant `reproduced`,
and a mismatch SHALL record both estimates.

#### Scenario: Matching estimate
- **WHEN** the example claim is reproduced with its script and data
- **THEN** the record grants `reproduced` and holds the estimate, the seed and the image digest

#### Scenario: Wrong data
- **WHEN** the data file's hash differs from the claim's
- **THEN** the step does not run and names both hashes

### Requirement: Robustness step
`test` SHALL run each variation declared with the claim and grant `robust` when the estimate keeps its sign and
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
