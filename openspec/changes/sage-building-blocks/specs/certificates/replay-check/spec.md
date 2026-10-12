# Spec Delta

## MODIFIED Requirements

### Requirement: Hygiene regression coverage
The test suite SHALL include, with replay enabled, `sage_run` examples covering: a refutation of a `≤` goal that introduces a fresh hypothesis, a context that contains an inaccessible hypothesis, and a certificate search over an empty constraint set.

#### Scenario: Regression suite
- **WHEN** `lake build VeriphyTest` runs with Sage available
- **THEN** the three regression examples elaborate and their replays pass
