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
`veriphy layers workflow next <workflow> <target>` SHALL compute the next step from the records whose inputs name the
target, read in time order, give the same answer for the same records, and print it with the exact command to type.
`veriphy layers workflow list` SHALL list the workspace's workflows with their steps.

#### Scenario: An agent step next
- **WHEN** no record names `Claim.lean` in `prove-claim`
- **THEN** `next` names `record-statement` as an agent step, and prints
  `veriphy layers step record-statement Claim.lean --by <your name>`

#### Scenario: After a counterexample
- **WHEN** the latest `sample` record of the target is a counterexample in `prove-claim`
- **THEN** `next` says the workflow stopped, naming the status `counterexample`

#### Scenario: Attempts exhausted
- **WHEN** `check` has been refused as many times as its `attempts` limit
- **THEN** `next` moves to the entry the workflow gives as `exhausted`, `stop` by default

#### Scenario: Listing
- **WHEN** `veriphy layers workflow list` runs with the default config
- **THEN** it lists `prove-claim` and `verify-paper`, each with its steps in order

#### Scenario: Back to an earlier entry
- **WHEN** `check` is refused and its transition goes back to `record-statement`
- **THEN** `next` answers `record-statement` until a newer `record-statement` record exists

### Requirement: Run until the agent
`veriphy layers workflow run <workflow> <target>` SHALL run every step that is not an agent step in order until the
next step is an agent step or the workflow stops, print each step's result as the step command does, and end with what
the agent must provide. It SHALL take each step's inputs as options, by the input's name or its flag, repeated for a
repeatable input.

#### Scenario: Waiting for a proof
- **WHEN** `prove-claim` reaches `record-proof` for a target with no proof recorded
- **THEN** `run` stops and prints `veriphy layers step record-proof <file> --by <your name>`

#### Scenario: Inputs as options
- **WHEN** `veriphy layers workflow run reproduce-analysis analysis.py --data survey.csv --variation "a" --variation "b"`
  reaches `robustness`
- **THEN** the step receives the data and both variations

### Requirement: Default workflows and skills
The `math` pack SHALL define `prove-claim` and `verify-paper`, and the `social-science` pack `reproduce-analysis`. The
skills SHALL use `next` and `run` to sequence their work, and their playbooks SHALL describe the agent steps.

#### Scenario: The prove skill
- **WHEN** the `prove` skill works on a claim
- **THEN** it takes the step `next` names, and its report cites the records
