# Spec Delta

## MODIFIED Requirements

### Requirement: Existing tactics preserve their interface
`sage_factor`, `sage_sos` (with or without hints), `sage_lincomb`, `sage_witness`, `sage_sum`, `sage_farkas` and `sage_exists` SHALL keep their syntax and the goal shapes they accept. They SHALL close goals and leave residual goals exactly as before. Each one's replacement SHALL be produced by a checker family or by a preset script run through the script-tactic pipeline, with the same axiom guard and replay check.

#### Scenario: Existing test file still passes
- **WHEN** `lake build VeriphyTest` runs with the components in place
- **THEN** every pre-existing example in `VeriphyTest.lean` elaborates without edits to its tactic calls

#### Scenario: Preset is readable
- **WHEN** the agent wants to adapt `sage_farkas` to a related goal
- **THEN** the preset script behind it ships in the installed package and can be read and reused as a `sage_run` script
