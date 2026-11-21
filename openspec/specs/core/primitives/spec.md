# core/primitives Specification

## Purpose
Run every operation Veriphy relies on as a primitive: typed by input and output schemas, pinned, of a declared trust class, deterministic for a given input and seed, and run as a Python function, a JSON-RPC 2.0 tool over stdio, or a command writing one JSON result, with no protocol of Veriphy's own.

## Requirements

### Requirement: Tools
A tool entry SHALL name its `contract` (`jsonrpc` or `files`), its `run` command as an argument list, its `pin` and its
`timeout`. Input values SHALL reach a tool as files or inside JSON messages, never interpolated into a shell command.

#### Scenario: A value with shell syntax
- **WHEN** a primitive's input holds the string `; rm -rf ~`
- **THEN** the tool receives it as data, and no shell interprets it

### Requirement: Primitives
A primitive entry SHALL name a Python `function`, or its tool and that tool's `method` or `command`, its trust class (`kernel`, `checker`,
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

### Requirement: Python primitives
A primitive with a `function` SHALL be called in-process, with the same schema checks as any primitive, and its
output SHALL name Veriphy's version as its tool's.

#### Scenario: No process for Python code
- **WHEN** `shacl.validate` runs
- **THEN** no process is started, and the output's tools name `veriphy`

### Requirement: JSON-RPC contract
A `jsonrpc` tool SHALL run as one process per session, speaking JSON-RPC 2.0 over stdio with one message per line.
The Sage session SHALL answer JSON-RPC 2.0 requests, and SHALL still answer requests without `"jsonrpc"` in the format of
earlier releases.

#### Scenario: Sage behind the contract
- **WHEN** the `math` pack's `sage` tool answers `ping`
- **THEN** the response is a JSON-RPC 2.0 result carrying Sage's and Veriphy's versions

#### Scenario: An error
- **WHEN** a request names a method the Sage session does not have
- **THEN** the response carries `error` with a code and a message naming the known methods

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
`veriphy layers primitive list` SHALL name every available primitive with its trust class and pack, `describe` SHALL
print one primitive's schemas, tool, pin and class, and `run <primitive> --input <file>` SHALL print its output as
JSON. A primitive whose tool is missing SHALL be listed as unavailable with the reason.

#### Scenario: By hand
- **WHEN** a person runs `veriphy layers primitive run sage.sample --input problem.json` with a seed in the input
- **THEN** standard output holds the sampled values, and no record is written

#### Scenario: No Lean installed
- **WHEN** `lake` is not on the path
- **THEN** `primitive list` shows `lean.check` as unavailable, naming `lake`, and the `core` primitives as available

### Requirement: Shipped primitives
Veriphy SHALL ship the packs `core` (`horn.check`, `shacl.validate`), `lean` (`lean.check`,
`lean.serialize`, `lean.level`) and `math` (the `sage` tool, one `sage.*` primitive per Sage method, and the
composites `meaning` and `certify`), each as a `pack.yaml` found through the `veriphy.packs` entry point. `math` SHALL
need `lean`, and `core` SHALL NOT need Lean.

#### Scenario: Every Sage method is a primitive
- **WHEN** the Sage session's methods are compared with the `math` pack's primitives
- **THEN** each method has a `sage.*` primitive with an input and an output schema

### Requirement: Lean REPL
The Lean primitives SHALL run in the community Lean REPL, pinned by commit, keeping one environment per import header,
and SHALL give the same output as running `lake env lean` on the same file.

#### Scenario: Two checks, one load
- **WHEN** `lean.check` runs on two files that both import only `Mathlib`, in one process
- **THEN** Mathlib is loaded once, and each output equals that of `lake env lean --json` on the file

### Requirement: Unchanged behaviour
The steps `check`, `level`, `meaning`, `validate` and `reason` SHALL call primitives and give the same records as
before. The Lean bridge SHALL take the Sage command from the `math` pack, and `VERIPHY_SAGE_CMD` and
`VERIPHY_SAGE_SESSION` SHALL still override it.

#### Scenario: A user's workspace
- **WHEN** a workspace with no `veriphy.yaml` runs `veriphy certify` and `veriphy layers step meaning`
- **THEN** it starts the same Sage session as before, and the meaning record has the same outcome and outputs
