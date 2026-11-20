# Spec Delta

## ADDED Requirements

### Requirement: Workflow schema
A workflow in the config SHALL be an ordered list of entries, each a step name or a step with transitions from status
to the next entry or `stop`, an optional `attempts` limit and an optional `when` condition. `config check` SHALL refuse
a workflow that names an undefined step.

#### Scenario: Undefined step
- **WHEN** a workflow names `certfy`
- **THEN** `config check` fails and names the workflow and the step

### Requirement: Next step from records
`python -m veriphy next <workflow> <target>` SHALL compute the next step from the target's records alone, and SHALL
give the same answer for the same records.

#### Scenario: After a counterexample
- **WHEN** the latest `meaning` record of the target is a counterexample in `prove-claim`
- **THEN** `next` answers `stop` with the reason `statement-suspect`

#### Scenario: Attempts exhausted
- **WHEN** `certify` has been refused as many times as its `attempts` limit
- **THEN** `next` moves to the entry the workflow gives for that case

### Requirement: Run until the agent
`python -m veriphy run <workflow> <target>` SHALL run every non-agent step in order until the next step is an agent
step or the workflow stops, and SHALL say what the agent must provide.

#### Scenario: Waiting for a script
- **WHEN** `prove-claim` reaches `search` for a target with no script
- **THEN** `run` stops and asks for a script for that goal

### Requirement: Default workflows and skills
The `math` pack SHALL define `prove-claim` and `verify-paper`, and the `reproduction` pack `reproduce-analysis`. The
skills SHALL use `next` and `run` to sequence their work, and their playbooks SHALL describe only the agent steps.

#### Scenario: The prove skill
- **WHEN** the `prove` skill works on a claim
- **THEN** every step it takes is the one `next` named, and its report cites the records
