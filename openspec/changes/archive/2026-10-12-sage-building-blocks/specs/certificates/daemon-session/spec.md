# Spec Delta

## Purpose

Makes the script-then-check loop fast. One Sage daemon serves every request from a Lean process instead of starting Sage for each tactic call, and it fails safe.

## ADDED Requirements

### Requirement: One daemon per Lean process
The bridge SHALL start the daemon on the first request in a Lean process and reuse it for later requests, so only the first call pays Sage's start-up time.

#### Scenario: Second call is fast
- **WHEN** two `sage_*` tactics run in one file
- **THEN** both are answered by the same daemon process

### Requirement: Recovery
If the daemon has exited or its pipe has broken, the bridge SHALL start a new one and retry the request once. If the retry fails, it SHALL report the start-up failure as the daemon-resolution spec describes.

#### Scenario: Daemon crashed
- **WHEN** the daemon process is killed between two tactic calls
- **THEN** the second call starts a new daemon and succeeds

### Requirement: Bounded requests
Each request SHALL have a time limit. A request that exceeds it SHALL fail with an error naming the limit. The daemon SHALL then be replaced, so a hung script cannot block later calls.

#### Scenario: Runaway script
- **WHEN** a `sage_run` script loops forever
- **THEN** the tactic fails after the limit with an error naming it, and the next tactic call gets a fresh daemon

### Requirement: No state leaks between requests
A script SHALL NOT see names, assumptions or results left by an earlier request.

#### Scenario: Assumption from an earlier call
- **WHEN** an earlier script ran `assume(x > 0)` and a later script checks a sign condition on `x`
- **THEN** the later script runs without that assumption

### Requirement: Replay stays offline
During replay, the bridge SHALL refuse requests without contacting the daemon, whether or not a session is open.

#### Scenario: Replay with a warm session
- **WHEN** a session is running and a replacement under replay tries to reach Sage
- **THEN** the request fails with the "bridge is disabled during replay" error
