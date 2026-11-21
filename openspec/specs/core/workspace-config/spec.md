# core/workspace-config Specification

## Purpose
Configure a workspace with one optional `veriphy.yaml` that selects packs, by name or path, and overrides any entry; packs load in the order they require and merge as JSON Merge Patches (RFC 7396), and the digest of the resolved configuration enters every record.

## Requirements

### Requirement: Workspace file
A workspace MAY hold `veriphy.yaml` at its root, with `version: 1` and the optional keys `packs`, `tools`,
`primitives`, `scopes`, `steps`, `levels`, `conventions`, `workflows` and `playbooks`. Without the file, the workspace
SHALL behave as with `packs: [math]`. Unknown keys SHALL be errors naming the key and its path.

#### Scenario: No file
- **WHEN** a workspace has no `veriphy.yaml`
- **THEN** `veriphy config show` lists the packs `core`, `lean` and `math` and their primitives

#### Scenario: A typo
- **WHEN** the file has the key `tool:` instead of `tools:`
- **THEN** `config check` fails and names the key

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
The resolved config SHALL be each pack in order, then the workspace file, each applied as a JSON Merge Patch (RFC
7396): mappings merge recursively, later values win, and `null` removes an entry.

#### Scenario: Removing a tool
- **WHEN** the workspace file sets `tools: {sage: null}`
- **THEN** the resolved config has no `sage`, and every primitive and step that needs it is reported unavailable

### Requirement: Collisions
When two packs that do not require each other define the same entry, `config check` SHALL fail naming both packs and
the entry, unless the workspace file defines that entry itself.

#### Scenario: Two packs define one step
- **WHEN** two unrelated local packs both define the step `test`
- **THEN** `config check` names both packs and `steps.test`, and passes once `veriphy.yaml` defines `steps.test`

### Requirement: Sections per layer
Each layer SHALL read only its own sections of the resolved config, and the `primitive` command and the steps SHALL
see only the selected packs' primitives and steps.

#### Scenario: Unselected pack
- **WHEN** a workspace lists `packs: [core]` and the `math` pack is installed
- **THEN** `veriphy primitive list` shows no `sage.*` primitive

### Requirement: Config commands and digest
`veriphy config show` SHALL print the resolved config with the pack or file each value comes from, and
`config check` SHALL validate it against the schema and check that every reference between sections resolves. The digest of the resolved config as canonical JSON SHALL enter every
step record's input digest.

#### Scenario: A pin changes
- **WHEN** the workspace pins a different SageMath version
- **THEN** the next run of a step that uses Sage gets a new digest instead of replaying

#### Scenario: A comment changes
- **WHEN** only a comment in `veriphy.yaml` changes
- **THEN** every record still replays
