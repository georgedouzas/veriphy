# certificates/sage-session Specification

## Purpose
Makes the script-then-check loop fast. One Sage session serves every request from a Lean process instead of starting Sage for each tactic call, and it fails safe.

## Requirements

### Requirement: One Sage session per Lean process
The bridge SHALL start the Sage session on the first request in a Lean process and reuse it for later requests, so only the first call pays Sage's start-up time.

#### Scenario: Second call is fast
- **WHEN** two `sage_*` tactics run in one file
- **THEN** both are answered by the same Sage session process

### Requirement: Recovery
If the Sage session has exited or its pipe has broken, the bridge SHALL start a new one and retry the request once. If the retry fails, it SHALL report the start-up failure as the sage-resolution spec describes.

#### Scenario: Sage session crashed
- **WHEN** the Sage session process is killed between two tactic calls
- **THEN** the second call starts a new Sage session and succeeds

### Requirement: Bounded requests
Each request SHALL have a time limit. A request that exceeds it SHALL fail with an error naming the limit. The Sage session SHALL then be replaced, so a hung script cannot block later calls.

#### Scenario: Runaway script
- **WHEN** a `veriphy certify` script loops forever
- **THEN** the tactic fails after the limit with an error naming it, and the next tactic call gets a fresh Sage session

### Requirement: No state leaks between requests
A script SHALL NOT see names, assumptions or results left by an earlier request.

#### Scenario: Assumption from an earlier call
- **WHEN** an earlier script ran `assume(x > 0)` and a later script checks a sign condition on `x`
- **THEN** the later script runs without that assumption

### Requirement: Replay stays offline
During replay, the bridge SHALL refuse requests without contacting the Sage session, whether or not a session is open.

#### Scenario: Replay with a warm session
- **WHEN** a session is running and a replacement under replay tries to reach Sage
- **THEN** the request fails with the "bridge is disabled during replay" error
