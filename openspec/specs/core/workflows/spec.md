# core/workflows Specification

## Purpose
Describe a workflow as data, a list of steps with what each record's status does next, so that `veriphy layers workflow next` names the next step for a target from its records alone, in time order, and `veriphy layers workflow run` runs the steps that are not an agent's until one is needed.

## Requirements

### Requirement: Workflow schema
A workflow, declared by a pack or the workspace file, SHALL be an ordered list of entries, each a step name or a step
with transitions from a record status to `stop` or to another entry by its step's name, an optional `attempts` limit
with an `exhausted` destination, and an optional `when` condition. `config check` SHALL refuse a workflow that names
an undefined step, or a transition to an entry the workflow does not have.

#### Scenario: Undefined step
- **WHEN** a workflow names `certfy`
- **THEN** `config check` fails and names the workflow and the step

### Requirement: Next step from records
`veriphy layers workflow next <workflow> <target>` SHALL compute the next step from the records whose inputs name the target, read in
time order, and SHALL give the same answer for the same records.

#### Scenario: After a counterexample
- **WHEN** the latest `meaning` record of the target is a counterexample in `prove-claim`
- **THEN** `next` answers `stop`, naming the status `counterexample`

#### Scenario: Attempts exhausted
- **WHEN** `check` has been refused as many times as its `attempts` limit
- **THEN** `next` moves to the entry the workflow gives as `exhausted`, `stop` by default

#### Scenario: Back to an earlier entry
- **WHEN** `check` is refused and its transition goes back to `formalize`
- **THEN** `next` answers `formalize` until a newer `formalize` record exists

### Requirement: Run until the agent
`veriphy layers workflow run <workflow> <target>` SHALL run every step that is not an agent step in order until the next step is an
agent step or the workflow stops, and SHALL say what the agent must provide.

#### Scenario: Waiting for a proof
- **WHEN** `prove-claim` reaches `prove` for a target with no proof recorded
- **THEN** `run` stops and asks for the proof of that target, as `veriphy layers step prove <file> --by agent`

### Requirement: Default workflows and skills
The `math` pack SHALL define `prove-claim` and `verify-paper`, and the `reproduction` pack `reproduce-analysis`. The
skills SHALL use `next` and `run` to sequence their work, and their playbooks SHALL describe the agent steps.

#### Scenario: The prove skill
- **WHEN** the `prove` skill works on a claim
- **THEN** it takes the step `next` names, and its report cites the records
