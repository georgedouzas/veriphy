# Spec Delta

## ADDED Requirements

### Requirement: Workspace file
A workspace MAY hold `veriphy.yaml` at its root, with `version: 1` and the optional keys `packs`, `tools`,
`primitives`, `scopes`, `steps`, `levels`, `conventions`, `workflows` and `playbooks`. Without the file, the workspace
SHALL behave as with `packs: [math]`. Unknown keys SHALL be errors naming the key and its line.

#### Scenario: No file
- **WHEN** a workspace has no `veriphy.yaml`
- **THEN** `python -m veriphy config show` lists the packs `core`, `lean` and `math` and their primitives

#### Scenario: A typo
- **WHEN** the file has the key `tool:` instead of `tools:`
- **THEN** `config check` fails and names the key and the line

### Requirement: Packs
An entry of `packs` SHALL be a name, resolved through the `veriphy.packs` entry point, or a path to a directory
holding a `pack.yaml` in the workspace file's schema with `name` and `requires` added. Each pack SHALL be loaded after
the packs it requires, which are loaded even when not listed.

#### Scenario: Requirements are loaded
- **WHEN** a workspace lists `packs: [math]`
- **THEN** the resolved config holds the `core`, `lean` and `math` packs, in that order

#### Scenario: A field without Lean
- **WHEN** a workspace lists `packs: [core, ./packs/econ]` and the local pack requires only `core`
- **THEN** the resolved config holds that pack's entries and no Lean or SageMath primitive

### Requirement: Merge
The resolved config SHALL be the core defaults, then each pack in order, then the workspace file. Mappings SHALL merge
key by key with later values winning, and `null` SHALL remove an entry.

#### Scenario: Removing a tool
- **WHEN** the workspace file sets `tools: {sage: null}`
- **THEN** the resolved config has no `sage`, and every primitive and step that needs it is reported unavailable

### Requirement: Collisions
When two packs that do not require each other define the same entry, `config check` SHALL fail naming both packs and
the entry, unless the workspace file defines that entry itself.

#### Scenario: Two packs define one step
- **WHEN** two unrelated local packs both define the step `test`
- **THEN** `config check` names both packs and `steps.test`, and passes once `veriphy.yaml` defines `steps.test`

### Requirement: Registries
The resolved config SHALL fill one registry per layer: primitives, steps, claims, workflows and playbooks. Each layer
SHALL receive only its own registry, and the `primitive` command and the steps SHALL see only the selected packs.

#### Scenario: Unselected pack
- **WHEN** a workspace lists `packs: [core]` and the `math` pack is installed
- **THEN** `python -m veriphy primitive list` shows no `sage.*` primitive

### Requirement: Config commands and digest
`python -m veriphy config show` SHALL print the resolved config with the pack or file each value comes from, and
`config check` SHALL run every layer's checks. The digest of the resolved config as canonical JSON SHALL enter every
step record's input digest.

#### Scenario: A pin changes
- **WHEN** the workspace pins a different SageMath version
- **THEN** the next run of a step that uses Sage gets a new digest instead of replaying

#### Scenario: A comment changes
- **WHEN** only a comment in `veriphy.yaml` changes
- **THEN** every record still replays
