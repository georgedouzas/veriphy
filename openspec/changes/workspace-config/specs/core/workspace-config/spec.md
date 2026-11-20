# Spec Delta

## ADDED Requirements

### Requirement: Workspace file
A workspace MAY hold `veriphy.yaml` at its root, with `version: 1` and the optional keys `packs`, `tools`, `levels`,
`steps`, `conventions` and `workflows`. Without the file, the workspace SHALL behave as with `packs: [math]`. Unknown
keys SHALL be errors.

#### Scenario: No file
- **WHEN** a workspace has no `veriphy.yaml`
- **THEN** `python -m veriphy config show` prints the `math` pack's tools, levels and workflows

#### Scenario: A typo
- **WHEN** the file has the key `tool:` instead of `tools:`
- **THEN** `config check` fails and names the key and the line

### Requirement: Packs
An entry of `packs` SHALL be either a name, resolved through the `veriphy.packs` entry point, or a path to a directory
holding `pack.yaml` in the workspace file's schema. Veriphy SHALL ship the packs `core` (Lean, the claim graph,
`oo-horn`) and `math` (`core` plus SageMath, the recipes and the five Lean levels).

#### Scenario: A local pack
- **WHEN** `packs: [core, ./packs/econ]` names a directory with a `pack.yaml`
- **THEN** the resolved config holds that pack's tools and levels

### Requirement: Merge order
The resolved config SHALL be the core defaults, then each pack in the listed order, then the workspace file. Mappings
SHALL merge key by key with later values winning, and `null` SHALL remove a key.

#### Scenario: Removing a tool
- **WHEN** the workspace file sets `tools: {sage: null}`
- **THEN** the resolved config has no `sage`, and a step that needs it is reported unavailable instead of running

### Requirement: Trust classes and levels
Every tool and level SHALL name one of the trust classes `kernel`, `checker`, `reproduction`, `oracle`, `measurement`
or `search`. Each level SHALL name the level directly below it, and the levels SHALL form one chain from `none`. A step
SHALL grant only levels of its tool's trust class.

#### Scenario: A branching order
- **WHEN** two levels both declare `above: none`
- **THEN** `config check` fails and names both

#### Scenario: Wrong class
- **WHEN** a step with an R tool of class `reproduction` declares `grants: lean-proof`
- **THEN** `config check` fails, naming the step, the level and both classes

### Requirement: Config commands and digest
`python -m veriphy config show` SHALL print the resolved config with the source of every value, and `config check`
SHALL validate it. The digest of the resolved config SHALL enter every step record's input digest.

#### Scenario: Config change invalidates records
- **WHEN** the workspace pins a different SageMath version
- **THEN** the next run of a step that uses Sage gets a new digest instead of replaying
