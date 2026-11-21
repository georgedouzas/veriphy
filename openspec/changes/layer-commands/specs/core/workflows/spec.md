## MODIFIED Requirements

### Requirement: Next step from records
`veriphy layers workflow next <workflow> <target>` SHALL compute the next step from the records whose inputs name the
target, read in time order, and SHALL give the same answer for the same records. `veriphy layers workflow list` SHALL list
the workspace's workflows with their steps.

#### Scenario: After a counterexample
- **WHEN** the latest `meaning` record of the target is a counterexample in `prove-claim`
- **THEN** `next` answers `stop`, naming the status `counterexample`

#### Scenario: Attempts exhausted
- **WHEN** `check` has been refused as many times as its `attempts` limit
- **THEN** `next` moves to the entry the workflow gives as `exhausted`, `stop` by default

#### Scenario: Back to an earlier entry
- **WHEN** `check` is refused and its transition goes back to `formalize`
- **THEN** `next` answers `formalize` until a newer `formalize` record exists

#### Scenario: Listing
- **WHEN** `veriphy layers workflow list` runs with the default config
- **THEN** it lists `prove-claim` and `verify-paper`, each with its steps in order

### Requirement: Run until the agent
`veriphy layers workflow run <workflow> <target>` SHALL run every step that is not an agent step in order until the next
step is an agent step or the workflow stops, and SHALL say what the agent must provide.

#### Scenario: Waiting for a proof
- **WHEN** `prove-claim` reaches `prove` for a target with no proof recorded
- **THEN** `run` stops and asks for the proof of that target, as `veriphy layers step prove <file> --by agent`
