# Design

## Context

After the earlier changes, every step is a primitive with inputs or a Python step of its layer, declared or registered
by a pack, and every run writes a record. Agent steps (`formalize`, `extract`) record an artifact. Claims take their
levels from records. The playbooks still sequence the steps in prose, with budgets ("stop after about 30 minutes or 3
attempts") the agent counts itself.

## Goals / Non-Goals

**Goals:**

- The next step is computed from the records, not interpreted.
- Agents keep the parts that need judgment, and nothing else.

**Non-Goals:**

- A general workflow engine with parallelism or loops beyond retries. Workflows are short sequences, and their
  decisions read records.

## Decisions

### D1. A workflow is a list of entries

An entry is a step name, or a step with a mapping: a record status to `stop` or to another entry of the workflow by
its step's name, `attempts` (how many records of the step the target may have), `exhausted` (where to go when they
are used up), and `when` (a condition). Without a transition, the next entry follows. A step may appear twice, as
`check` before and after the agent's proof.

```yaml
workflows:
  prove-claim:
    - formalize
    - meaning: {counterexample: stop}
    - check: {refused: formalize, attempts: 3}
    - prove
    - check: {refused: prove, attempts: 5}
    - level
```

### D2. The position comes from the records, read in time order

A target is a value the steps' inputs name, such as a Lean file. A record belongs to the target when one of its inputs
names it. `next` walks the entries from the start, consuming at each entry the latest record of its step for the
target that is newer than the record consumed before it; with none, that entry is the next step. So a return to an
earlier entry needs a new record, and the same records always give the same answer. Nothing else is stored, so
deleting records moves the workflow back.

### D3. `run` stops at agent steps

`run` executes the steps that are not agent steps until the next one is an agent step or the workflow stops, and says
what the agent must provide. A step's inputs come from `--input name=value`, and its first input defaults to the
target. An agent step is done when its artifact is recorded.

### D4. Conditions read records only

`when: {without: <class>}` holds when no record for the target grants a level of that trust class, as
`when: {without: kernel}` to test a claim only when nothing proved it. (The key is not `no`, which YAML reads as
`false`.) A condition reads nothing but records, so `next`
stays a function of them.

### D5. Attempts are counted from records

The number of records of a step for the target is its attempt count, so the budget is enforced by the engine, not by
the agent. When it is used up, `exhausted` names where to go, `stop` by default.

## Risks / Trade-offs

- [Prose guidance lost] → The playbooks keep it for agent steps, and each skill says to follow `next`.
- [Records of abandoned attempts] → They count as attempts by design, so a budget means what it says.
