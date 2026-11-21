# Spec Delta

## MODIFIED Requirements

### Requirement: Shell command and Python function
`veriphy <verb> <target> [inputs]` SHALL run the verb's step, the same as `python -m veriphy <verb>`, and
`veriphy.run(verb, target, **inputs)` SHALL return the same result as a `Result`. `veriphy claims`, `veriphy agents`,
`veriphy records`, `veriphy primitive`, `veriphy config`, `veriphy certificates` and `veriphy translations` SHALL
replace the per-module programs. The `veriphy` command SHALL be one click group, whose subcommands the layers and packs
contribute, with a command per registered step of the workspace.

#### Scenario: Same result from both
- **WHEN** `veriphy check Claim.lean` and `veriphy.run("check", "Claim.lean")` run on one file
- **THEN** both give the same status and the same record

#### Scenario: Help generated from a step
- **WHEN** a user runs `veriphy meaning --help`
- **THEN** it lists the step's arguments and options, `--seed`, `--values`, `--points` and `--informal` among them
