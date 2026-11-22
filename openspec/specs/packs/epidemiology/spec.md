# packs/epidemiology Specification

## Purpose
TBD - created by archiving change domain-packs. Update Purpose after archive.

## Requirements

### Requirement: Epidemiology pack
Veriphy SHALL ship an `epidemiology` pack, requiring `statistics`, whose steps use lifelines: `check-hazard-ratio`
refits a Cox model and compares the first covariate's hazard ratio with the claim, and `check-median-survival`
recomputes a Kaplan-Meier median for the subjects of a group. Both SHALL grant `recomputed`. A median that is not
reached SHALL fail.

#### Scenario: The example trial
- **WHEN** the example's hazard ratio for treatment, adjusted for age, is claimed as 0.63
- **THEN** the check agrees, recording the 95% interval and the subjects and events counted
