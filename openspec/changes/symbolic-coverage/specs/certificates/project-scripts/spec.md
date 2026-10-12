# Spec Delta

## MODIFIED Requirements

### Requirement: Scripts live in the caller's project
Certificate scripts SHALL be stored as `.sage` files in `.veriphy/certificates/` at the root of the project being proved, never in the Veriphy repository or package. `sage_run file "<path>"` SHALL run a script file. A bare file name (no directory) SHALL resolve in `.veriphy/certificates/`, and any other relative path SHALL resolve against the Lean workspace root.

#### Scenario: Run a saved script
- **WHEN** a proof in a downstream project uses `sage_run file "anomaly_farkas.sage"`
- **THEN** the script `.veriphy/certificates/anomaly_farkas.sage` runs against the current goal, and the emitted replacement is the plain Lean proof

#### Scenario: Explicit path
- **WHEN** a proof uses `sage_run file ".veriphy/certificates/anomaly_farkas.sage"`
- **THEN** the same script runs

#### Scenario: Missing file
- **WHEN** the path names no file
- **THEN** the tactic fails with an error naming the resolved path, without contacting Sage

### Requirement: Discoverable catalog
`sage -python -m veriphy.certificates list [--root DIR]` SHALL print one line per script in `.veriphy/certificates/` of the workspace: name, technique, goal shape and description. `… show <name>` SHALL print one script.

#### Scenario: Agent discovers existing scripts
- **WHEN** an agent runs the list command in a project with three saved scripts
- **THEN** it sees three entries, and can print any of them by name

### Requirement: Reuse before writing, save after success
The `prove` and `certify` workflows SHALL direct the agent to consult the project's catalog before writing a new script, to adapt a matching script when one exists, and to save a script that closed its goal, with a complete header, into `.veriphy/certificates/`. Translation entries go into `.veriphy/translations/`, and copied Lean assets into `.veriphy/lean/`.

#### Scenario: Second similar goal
- **WHEN** the agent meets a goal of the same shape as a saved script's
- **THEN** the workflow leads it to run or adapt that script rather than write one from scratch
