# Spec Delta

## Purpose

Automatically checks Veriphy's core promise: every emitted `Try this:` replacement is exactly the text a user would commit, and that text re-parses and closes the original goal with no Sage installed.

## ADDED Requirements

### Requirement: Opt-in replay option
The system SHALL provide a Lean option `veriphy.checkReplay` (default `false`). When it is `true`, every replacement emitted through a checker family SHALL be replay-checked before the tactic succeeds.

#### Scenario: Option off
- **WHEN** `veriphy.checkReplay` is unset
- **THEN** tactics behave as they did before, with no replay overhead

#### Scenario: Option on in the test suite
- **WHEN** `VeriphyTest.lean` sets `set_option veriphy.checkReplay true`
- **THEN** every `sage_*` call in the file is replay-checked

### Requirement: Replay from printed text
A replay SHALL pretty-print the replacement to a string and parse that string as a tactic in the current environment. It SHALL then run it on the goal as it was before the tactic ran. The replay passes only if parsing succeeds and the resulting goals match the goals the tactic itself left.

#### Scenario: Hygienic name in the printed proof
- **WHEN** a replacement prints a hypothesis as `hfk✝`
- **THEN** the replay fails at parsing, and the tactic errors with the printed text in the message

#### Scenario: Printed proof closes a different set of goals
- **WHEN** the tactic closes the goal but the re-parsed replacement leaves a goal open
- **THEN** the tactic errors, reporting the replay mismatch and the leftover goal

### Requirement: Replay without the oracle
During a replay the Sage bridge SHALL be disabled, so any daemon request fails immediately. A replacement that still calls Sage therefore fails the replay.

#### Scenario: Replacement that re-invokes a sage tactic
- **WHEN** a replacement accidentally contains a `sage_*` call that reaches the daemon
- **THEN** the replay fails with an error stating that the bridge is disabled during replay

### Requirement: Replay leaves no trace
A replay SHALL run in a saved and restored state. It SHALL NOT change the tactic's resulting proof term, goals, messages or emitted suggestion.

#### Scenario: Successful replay
- **WHEN** the replay passes
- **THEN** the elaborated proof and the single `Try this:` suggestion are identical to a run with the option off

### Requirement: Hygiene regression coverage
The test suite SHALL include, with replay enabled:
- a goal that needs a negation step with a fresh hypothesis (`sage_farkas` on `u ≤ 0`);
- a context that contains an inaccessible hypothesis;
- a certificate search over an empty constraint set.

#### Scenario: Regression suite
- **WHEN** `lake build VeriphyTest` runs with Sage available
- **THEN** the three regression examples elaborate and their replays pass
