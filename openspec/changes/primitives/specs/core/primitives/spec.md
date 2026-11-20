# Spec Delta

## ADDED Requirements

### Requirement: Tools
A tool entry SHALL name its `contract` (`files` or `json-lines`), its `run` command as an argument list, its `pin` and
its `timeout`. Input values SHALL reach a tool as files or inside JSON requests, never interpolated into a shell
command.

#### Scenario: A value with shell syntax
- **WHEN** a primitive's input holds the string `; rm -rf ~`
- **THEN** the tool receives it as data, and no shell interprets it

### Requirement: Primitives
A primitive entry SHALL name its tool, its `method` or `command`, its trust class (`kernel`, `checker`,
`reproduction`, `oracle`, `measurement` or `search`), an input schema and an output schema, and `seed` when it uses
randomness. Its input SHALL be checked against the input schema before the tool is started, and its output against
the output schema.

#### Scenario: Invalid input
- **WHEN** `sage.sample` is called with `values: "ten"`
- **THEN** it refuses before starting Sage, and the error names the field `values` and the expected type

#### Scenario: Drifting output
- **WHEN** a tool answers with an output that lacks a field its schema requires
- **THEN** the call fails and names the primitive and the missing field

### Requirement: Files contract
A `files` tool SHALL read its inputs from the paths in its placeholders and write one JSON object to `{out}`. A missing
or malformed result SHALL fail the call with the tool's standard error.

#### Scenario: No result
- **WHEN** a files tool exits with status 0 but writes no `{out}`
- **THEN** the call fails, holding the tool's standard error

### Requirement: JSON-lines contract
A `json-lines` tool SHALL run as one process per session, read one JSON request per line and write one JSON response
per line.

#### Scenario: Sage behind the contract
- **WHEN** the `math` pack's `sage` tool answers `ping`
- **THEN** the response carries Sage's and Veriphy's versions, as today

### Requirement: Pins
Before a tool runs, its pin (`image` with a digest, `commit` with `sha256`, or `version`) SHALL be checked. A tool that
does not match its pin SHALL NOT run. Every output SHALL carry the tool's name, the version found and the pin kind.

#### Scenario: Version drift
- **WHEN** the `sage` tool is pinned at `version: "10.9"` and Sage reports 10.8
- **THEN** no `sage.*` primitive runs, and the error names both versions

### Requirement: Determinism and purity
A primitive SHALL give the same output for the same input and seed. It SHALL NOT write records, and SHALL NOT read the
workspace's `.veriphy/` directory or `veriphy.yaml`.

#### Scenario: Two calls
- **WHEN** `sage.sample` runs twice on the same problem with seed 3
- **THEN** both outputs are equal, and `.veriphy/` is unchanged

### Requirement: Composites
A composite primitive SHALL be a deterministic composition of primitives that names the part that decides. Its trust
class SHALL be the deciding part's class, or the lowest class of its parts when no part decides. Each part SHALL be
called through the same checks as any primitive.

#### Scenario: Certify
- **WHEN** `primitive describe certify` runs
- **THEN** it names `sage.search` and `lean.check` as parts, `lean.check` as deciding, and the class `kernel`

#### Scenario: Meaning
- **WHEN** `primitive describe meaning` runs
- **THEN** it names `lean.serialize` and `sage.sample` as parts, none deciding, and the class `oracle`

### Requirement: Primitive command
`python -m veriphy primitive list` SHALL name every available primitive with its trust class and pack, `describe` SHALL
print one primitive's schemas, tool, pin and class, and `run <primitive> --input <file>` SHALL print its output as
JSON. A primitive whose tool is missing SHALL be listed as unavailable with the reason.

#### Scenario: By hand
- **WHEN** a person runs `python -m veriphy primitive run sage.sample --input problem.json` with a seed in the input
- **THEN** standard output holds the sampled values, and no record is written

#### Scenario: No Lean installed
- **WHEN** `lake` is not on the path
- **THEN** `primitive list` shows `lean.check` as unavailable, naming `lake`, and the `core` primitives as available

### Requirement: Shipped primitives
Veriphy SHALL ship the packs `core` (`oo-horn.check`, `shacl.validate`), `lean` (the Lean session, `lean.check`,
`lean.serialize`, `lean.levels`) and `math` (the `sage` tool, one `sage.*` primitive per daemon method, and the
composites `meaning` and `certify`), each as a `pack.yaml` found through the `veriphy.packs` entry point. `math` SHALL
need `lean`, and `core` SHALL NOT need Lean.

#### Scenario: Every daemon method is a primitive
- **WHEN** the daemon's methods are compared with the `math` pack's primitives
- **THEN** each method has a `sage.*` primitive with an input and an output schema

### Requirement: Lean session
The `lean` tool SHALL keep a file's imports loaded across requests with the same import header, and Lean primitives
SHALL give the same output as running `lake env lean` on the same file.

#### Scenario: Two checks, one load
- **WHEN** `lean.check` runs on two files that both import only `Mathlib`, in one session
- **THEN** Mathlib is loaded once, and each output equals that of `lake env lean --json` on the file

### Requirement: Unchanged behaviour
The steps `elaborate`, `level`, `meaning`, `validate` and `reason` SHALL call primitives and give the same records as
before. The Lean bridge SHALL take the Sage command from the `math` pack, and `VERIPHY_SAGE_CMD` and
`VERIPHY_SAGE_SERVER` SHALL still override it.

#### Scenario: A user's workspace
- **WHEN** a workspace with no `veriphy.yaml` runs `sage_run` and `python -m veriphy meaning`
- **THEN** it starts the same daemon as before, and the meaning record has the same outcome and outputs
