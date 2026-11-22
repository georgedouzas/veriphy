# packs/social-science Specification

## Purpose
TBD - created by archiving change field-packs. Update Purpose after archive.

## Requirements

### Requirement: Social-science pack
Veriphy SHALL ship a `social-science` pack, needing no Lean and no SageMath, with the steps `reproduce`, `robustness`
and `check-concepts`, the levels `reproduced` and `robust` of the `reproduction` class, the conventions
`identification` and `sampling`, and the workflow `reproduce-analysis`.

#### Scenario: Selecting the pack
- **WHEN** a workspace lists `packs: [social-science]`
- **THEN** `veriphy config check` passes, and no `lean.*` or `sage.*` primitive is configured

### Requirement: Analysis in Python
The pack SHALL run an analysis script, defining `run(data, inputs)`, in a fresh Python process, with the data as rows
and `inputs['variation']`, the seed set before it runs, and SHALL record the data's SHA-256. Data whose digest differs
from a given `--sha256` SHALL be refused before the script runs.

#### Scenario: The example study
- **WHEN** `reproduce` runs the example's `analysis.py` on `survey.csv`, claiming 0.127
- **THEN** it reproduces 0.1265, agrees within the reported tolerance, and grants `reproduced`

### Requirement: Robustness
`robustness` SHALL rerun the analysis under each declared variation, granting `robust` when the estimate keeps its sign
and its significance at 5% under every one, and recording `fragile` with the variations that break it otherwise.

#### Scenario: A variation that breaks it
- **WHEN** one declared variation makes the estimate insignificant
- **THEN** the status is `fragile`, the record names that variation, and no level is granted

### Requirement: Concepts against a thesaurus
`check-concepts <thesaurus>` SHALL check that every `vp:Concept` of the claim graph is linked by `owl:sameAs` to a
concept the SKOS thesaurus defines, reporting the thesaurus's label for each, `conforms` when all are, and a violation
naming each construct that isn't. It SHALL grant no level.

#### Scenario: A construct the thesaurus lacks
- **WHEN** a construct names a concept the thesaurus does not define
- **THEN** the status is `violations`, naming the construct and the concept

### Requirement: Measures as conventions
How a construct is measured SHALL be a convention of one aspect per construct, so that a claim resting on two measures
of one construct is a clash once their exclusion is confirmed.

#### Scenario: Two measures of social trust
- **WHEN** the example's policy claim uses two claims that measure social trust differently
- **THEN** `veriphy layers claims clashes` reports the policy claim
