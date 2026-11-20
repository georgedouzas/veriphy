# Spec Delta

## ADDED Requirements

### Requirement: Step records
Every step SHALL write one JSON record to `.veriphy/runs/<step>/<digest>.json` holding the step name, its kind, the
input digest, the config digest, the tool versions, the seed when the step is random, the status, the outputs and,
for check and derived steps, the level it grants. A record SHALL NOT be edited after it is written.

#### Scenario: A level report
- **WHEN** `python -m veriphy level MyProject` runs in a workspace
- **THEN** a record under `.veriphy/runs/level/` lists each declaration with its level, and names the Lean version

#### Scenario: A failure is recorded
- **WHEN** `python -m veriphy elaborate MyProject/Broken.lean` runs on a file that does not type-check
- **THEN** the record has status `refused` and holds Lean's errors, and the command exits with status 1

### Requirement: Replay by digest
The input digest SHALL be the SHA-256 of the step name, the content of each input, the config digest and the seed.
When a record with that digest exists, the step SHALL return it without running a tool. With `--rerun` the step SHALL
run again, report whether the output changed, and keep both records when it did.

#### Scenario: Same inputs
- **WHEN** `python -m veriphy reason` runs twice on an unchanged graph
- **THEN** the second call returns the first record and starts no reasoner and no checker

#### Scenario: Moved file
- **WHEN** a source file moves to another path with the same content
- **THEN** its digest and its record stay the same

#### Scenario: Changed result on rerun
- **WHEN** `--rerun` gives a different output for the same digest
- **THEN** the command reports the difference and both records remain

### Requirement: Step kinds
Each step SHALL declare one kind: `agent` (it writes an artifact), `evidence` (it finds candidates or measures),
`check` (a trusted tool accepts or refuses) or `derived` (computed from other records). Only `check` and `derived`
records SHALL carry a level.

#### Scenario: Evidence carries no level
- **WHEN** `python -m veriphy validate` writes its record
- **THEN** the record has kind `evidence` and no `level` field

### Requirement: Step command
`python -m veriphy <step> [arguments]` SHALL run a step and print the record's path and status, or the record itself
with `--json`. It SHALL exit with status 0 on an accepting status, 1 on a refusal or counterexample, 2 on bad usage
and 3 on an unchecked result. `python -m veriphy records` SHALL list records and show one by digest.

#### Scenario: Machine-readable result
- **WHEN** an agent runs `python -m veriphy level MyProject --json`
- **THEN** it reads the full record from standard output, with no other text

### Requirement: First steps
The command SHALL provide `elaborate` (Lean checks a file and reports each declaration's axioms), `level` (the levels
`#veriphy_levels` reports), `validate` (the graph's shapes), `reason` (graph reasoning with the checker's verdict) and
`report` (the verification appendix). Each SHALL give the same result as the command it wraps.

#### Scenario: Reason through the step
- **WHEN** `python -m veriphy reason` runs on the fixture graph with `oo-horn` set up
- **THEN** the record's status is `entailed`, it names the run's certificate directory, and `python -m veriphy.graph
  recheck` on that directory agrees
