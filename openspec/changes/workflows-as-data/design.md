# Design

## Context

After the earlier changes, every step is declared in a pack and writes a record, agent steps record their artifacts,
and claims take their levels from records. The playbooks still sequence
the steps in prose, with budgets ("stop after about 30 minutes or 3 attempts") the agent counts itself.

## Goals / Non-Goals

**Goals:**

- The next step is computed, not interpreted.
- Agents keep the parts that need judgment, and nothing else.

**Non-Goals:**

- A general workflow engine with parallelism or loops beyond retries. Workflows are short sequences.

## Decisions

### D1. A workflow is a list with transitions

Each entry is a step name, or a step with a mapping from status to the next entry (`stop`, or another step), an
`attempts` limit, and a `when` condition on an earlier record. Without a transition, the next entry follows.

### D2. The position comes from the records

`next` finds, for the target, the latest record of each step in the workflow and replays the transitions from the
start. Nothing else is stored, so deleting a record moves the workflow back to that step.

### D3. `run` stops at agent steps

`run` executes `evidence`, `check` and `derived` steps until the next one is an `agent` step or the workflow stops, and
prints what the agent must provide. An agent step is done when its artifact is recorded, as `declarative-steps` defines.

### D4. Conditions read records and claims

A `when` condition reads the target's records or its claim's level, such as `no-certificate` (no record grants a
`kernel` level). It never reads anything else, so `next` stays a function of the records.

### D5. Attempts are counted from records

The number of records of a step for the target is its attempt count, so the budget is enforced by the engine, not by
the agent.

## Risks / Trade-offs

- [Prose guidance lost] → The playbooks keep it for agent steps, and each workflow entry links its playbook section.
- [Records of abandoned attempts] → They count as attempts by design, and `records --prune` cleans what is no longer
  referenced.
