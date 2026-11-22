# packs/particle-physics Specification

## Purpose
TBD - created by archiving change domain-packs. Update Purpose after archive.

## Requirements

### Requirement: Particle-physics pack
Veriphy SHALL ship a `particle-physics` pack, requiring `physics`, with the level `prediction-recomputed`
(reproduction) above `dimensionally-consistent`, the conventions `operator-basis` and `ckm-input`, and the workflow
`check-flavour`.

#### Scenario: Selecting the pack
- **WHEN** a workspace lists `packs: [particle-physics]`
- **THEN** the packs are `core`, `physics` and `particle-physics`, and `veriphy config check` passes

### Requirement: Predictions with flavio
`check-prediction` SHALL recompute an observable's prediction with flavio, in the Standard Model or with given Wilson
coefficients, with flavio's theory uncertainty from a seeded sample, and agree when the claim is within `sigmas` (2 by
default) combined uncertainties plus its rounding, granting `prediction-recomputed`.

#### Scenario: The Bs to mumu branching ratio
- **WHEN** a source claims BR(Bs→μμ) = 3.66 × 10⁻⁹ in the Standard Model
- **THEN** the check agrees; a claim of 2.9 × 10⁻⁹ differs and grants nothing

### Requirement: Running coefficients and PDG values
`run-coefficients` SHALL run Wilson coefficients to another scale with wilson, matching between effective theories,
and compare a coefficient with the claim, granting `prediction-recomputed`. `check-pdg` SHALL compare a particle's mass,
width or lifetime with the PDG tables of the `particle` package, as evidence.

#### Scenario: A mass given for the wrong meson
- **WHEN** `check-pdg "B(s)0" mass 5279.3` runs
- **THEN** the status is `differs`, with the PDG's 5366.92 MeV
