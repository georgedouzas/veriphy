# Spec Delta

## ADDED Requirements

### Requirement: Tool entries
A tool in the config SHALL name its `trust` class, its `contract` (`files` or `json-lines`), its `run` command with
placeholders, its `pin`, its `timeout`, and `seed` when it is random. Inputs SHALL reach the tool as files or JSON,
never interpolated into a shell command.

#### Scenario: A value with shell syntax
- **WHEN** an input value contains `; rm -rf ~`
- **THEN** the tool receives it as data in a file, and no shell interprets it

### Requirement: Files contract
A `files` tool SHALL read its inputs from the paths in its placeholders and write one JSON object to `{out}`. A missing
or malformed result SHALL give a record with status `failed` that holds the tool's output.

#### Scenario: Malformed result
- **WHEN** a files tool exits 0 but writes no `{out}`
- **THEN** the record's status is `failed` and it holds the tool's standard error

### Requirement: JSON-lines contract
A `json-lines` tool SHALL run as one process per session, read one JSON request per line and write one JSON response
per line, each response carrying the tool's version.

#### Scenario: Sage behind the contract
- **WHEN** the `math` pack's `sage` tool answers `ping`
- **THEN** the response carries Sage's and Veriphy's versions, as today

### Requirement: Pins checked at run time
Before running a tool, Veriphy SHALL check its pin (`image` with a digest, `commit` with `sha256`, or `version`) and
record the version found and the pin kind. A tool that does not match its pin SHALL NOT run.

#### Scenario: Version drift
- **WHEN** the config pins `sage` at `version: "10.9"` and Sage reports 10.8
- **THEN** the step does not run and its record names both versions

### Requirement: Sage and oo-horn as tools
The `math` pack SHALL declare `sage` as a `json-lines` tool of class `oracle`, and the `core` pack SHALL declare
`oo-horn` as a `files` tool of class `checker` with its pinned commit and hash. The Lean bridge SHALL take the Sage
command from the resolved config, and `VERIPHY_SAGE_CMD` SHALL still override it.

#### Scenario: Unchanged for users
- **WHEN** a workspace with no `veriphy.yaml` runs `sage_run`
- **THEN** it starts the same daemon as before this change
