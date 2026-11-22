## MODIFIED Requirements

### Requirement: Tools
A tool entry SHALL name its `contract`, `files`, its `run` command as an argument list, its `pin`, its `version`
probe and its `timeout`. Input values SHALL reach a tool as files, never interpolated into a shell command.

#### Scenario: A value with shell syntax
- **WHEN** a primitive's input holds the string `; rm -rf ~`
- **THEN** the tool receives it as data, and no shell interprets it

### Requirement: Primitives
A primitive entry SHALL name a Python `function`, or its tool and the `command` that follows the tool's, its trust
class (`kernel`, `checker`, `reproduction`, `oracle`, `measurement` or `search`), an input schema and an output schema,
and `seed` when it uses randomness. Its input SHALL be checked against the input schema before the tool is started,
and its output against the output schema.

#### Scenario: Invalid input
- **WHEN** `sage.sample` is called with `values: "ten"`
- **THEN** it refuses before starting Sage, and the error names the field `values` and the expected type

#### Scenario: Drifting output
- **WHEN** a tool answers with an output that lacks a field its schema requires
- **THEN** the call fails and names the primitive and the missing field

## ADDED Requirements

### Requirement: One process per call
Veriphy SHALL keep no process alive between primitive calls. A tool SHALL run once per call, and its version probe
SHALL run at most once per Veriphy process. Sage's methods SHALL run as
`sage -python -m veriphy.packs.math.primitives.sage call <method> <input> <out>`, and the Lean primitives SHALL run
`lake env lean` once per call. Only Lean itself SHALL keep a Sage session, while it compiles a file, speaking JSON-RPC
2.0 over its stdin and stdout.

#### Scenario: A Sage primitive
- **WHEN** `sage.ping` is called twice in one Veriphy process
- **THEN** Sage starts once for the version probe and once per call, and no Sage process remains afterwards

#### Scenario: A Lean primitive
- **WHEN** `lean.check` runs on a file
- **THEN** one `lake env lean` process runs and exits, and the output names the workspace's Lean as its tool

## REMOVED Requirements

### Requirement: JSON-RPC contract
**Reason**: Python makes one or two calls per command, so a kept Sage process saved nothing there; only Lean, which
makes many calls per file, keeps one.
**Migration**: A pack's tool is a `files` tool: a command that reads `{input}` and writes `{out}`.

### Requirement: Lean REPL
**Reason**: A command runs one or two Lean primitives, so keeping a REPL saved little and cost a build, a cache and a
second way to run Lean.
**Migration**: None: the Lean primitives give the same records, running `lake env lean` each time.
