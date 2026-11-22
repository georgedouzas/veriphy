## MODIFIED Requirements

### Requirement: Shell command and Python function
`veriphy layers step <verb> <target> [inputs]` SHALL run the verb's step, the same as `python -m veriphy layers step <verb>`, and
`veriphy.run(verb, target, **inputs)` SHALL return the same result as a `Result`.

#### Scenario: Same result from both
- **WHEN** `veriphy layers step check Claim.lean` and `veriphy.run("check", "Claim.lean")` run on one file
- **THEN** both give the same status and the same record

#### Scenario: Help generated from a step
- **WHEN** a user runs `veriphy layers step sample --help`
- **THEN** it lists the step's arguments and options, `--seed`, `--values`, `--points` and `--informal` among them

### Requirement: One click group
The `veriphy` command SHALL be one click group with four commands: `layers`, which holds one group per layer in layer
order (`primitive`, `step`, `claims`, `workflow`, `agents`); `config`; `pack`, which lists the selected packs and holds
one group per selected pack that declares programs; and `help`. It SHALL list the layer and pack groups without
importing their modules.

#### Scenario: The top level
- **WHEN** a user runs `veriphy --help` with the default config
- **THEN** it lists `config`, `help`, `layers` and `pack`, and nothing else

#### Scenario: The layers
- **WHEN** a user runs `veriphy layers --help`
- **THEN** it lists `primitive`, `step`, `claims`, `workflow` and `agents`, in that order

#### Scenario: A pack's step is a command
- **WHEN** a workspace uses the `reproduction` pack and a user runs `veriphy layers step --help`
- **THEN** `reproduce` and `vary` are listed beside the other steps, `list` and `records`
