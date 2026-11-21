# Spec Delta

## MODIFIED Requirements

### Requirement: Replay by digest
The input digest SHALL be the SHA-256 of the step name, the content of each input as its digest scope gives it, the
config digest and the seed. When a record with that digest and a final status exists, the step SHALL return it without
running a primitive. `unchecked` and `failed` are not final. With `--rerun` the step SHALL run again and keep both
records when the output changed.

#### Scenario: Same inputs
- **WHEN** `veriphy reason` runs twice on an unchanged graph
- **THEN** the second call returns the first record and starts no reasoner and no checker

#### Scenario: Moved file
- **WHEN** a source file moves to another path with the same content
- **THEN** its digest and its record stay the same

#### Scenario: Checker installed later
- **WHEN** `reason` was recorded as `unchecked` and the checker is set up afterwards
- **THEN** the next `reason` runs again instead of replaying the unchecked record

#### Scenario: Changed result on rerun
- **WHEN** `--rerun` gives a different output for the same digest
- **THEN** the command reports the difference and both records remain

### Requirement: First steps
The packs SHALL declare `check` (Lean checks a file and reports each declaration's axioms) and `level` (the levels
`#veriphy level` reports) in `lean`, `meaning` in `math`, and `validate` (the graph's shapes), `reason` (graph
reasoning with the checker's verdict) and `report` (the verification appendix) in `core`. Each SHALL give the same
result as before it was declared.

#### Scenario: Reason through the step
- **WHEN** `veriphy reason` runs on the fixture graph with `oo-horn` set up
- **THEN** the record's status is `entailed`, it names the run's certificate directory, and `veriphy claims
  recheck` on that directory agrees

#### Scenario: Lean steps without Lean
- **WHEN** a workspace lists `packs: [core]`
- **THEN** `check` and `level` are not steps of the workspace, and `reason` still runs
