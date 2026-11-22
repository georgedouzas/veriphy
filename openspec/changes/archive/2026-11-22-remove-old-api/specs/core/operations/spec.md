## REMOVED Requirements

### Requirement: Deprecated forms
**Reason**: The old forms were kept for one minor release so users could move; two spellings of every operation
double what users and agents learn and what the tests cover.
**Migration**: `sage_run` → `veriphy certify`, `sage_test` → `#veriphy test`, `#veriphy_<name>` → `#veriphy <verb>`
(`meaning`, `translations check`, `coverage`, `translate`, `export`, `translations`, `level`), `elaborate` → `check`,
`python -m veriphy.<module>` → `veriphy layers <layer>` or `veriphy pack math <program>`, and a script returns `found(...)` from `run(goal, inputs)`.

## ADDED Requirements

### Requirement: One spelling per operation
Each operation SHALL have one spelling in each place it runs: `veriphy <verb>` and `#veriphy <verb>` in Lean,
`veriphy layers step <verb>` in the shell and `veriphy.run` in Python. The removed names SHALL fail as unknown, not run.

#### Scenario: An old tactic
- **WHEN** a proof runs `sage_run file "sos.sage"`
- **THEN** Lean reports unknown syntax, and `veriphy certify "sos.sage"` closes the goal

#### Scenario: An old verb
- **WHEN** a user runs `veriphy layers step elaborate Claim.lean`
- **THEN** the command fails as an unknown command, listing the steps

#### Scenario: A script that assigns its result
- **WHEN** a script for `certify` assigns `proof = Lean.tactic("rfl")` and defines no `run`
- **THEN** the Sage session refuses it, saying to return `found(proof)` from `run(goal, inputs)`

#### Scenario: A request without JSON-RPC
- **WHEN** the Sage session receives `{"id": 1, "method": "ping"}`
- **THEN** it answers with the JSON-RPC 2.0 error code -32600 (invalid request)
