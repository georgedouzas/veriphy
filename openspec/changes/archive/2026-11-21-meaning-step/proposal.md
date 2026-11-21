# Proposal

## Why

The kernel cannot check that a formal statement means what the informal one said. The `prove` playbook guards that
step with a numeric test the agent improvises: random values, no seed, no record. It is the most important check that
has no tool. A wrong formalization that the agent never tested well produces a correct proof of the wrong statement.

## What Changes

- A Lean command, `#veriphy_meaning c`, and a step, `python -m veriphy meaning <file> <declaration>`, that evaluate a
  claim's statement at seeded values satisfying its hypotheses and the domain conditions of its functions.
- When the statement is an identity, `symbolic_check` runs first, and its answer is recorded.
- The outcome is `agrees` (with the number of values), `counterexample` (with the values and both sides) or
  `undecided` (too few values satisfied the hypotheses, or the statement could not be evaluated).
- The step is of kind `evidence` and grants no level. The `prove` playbook and the triage of `research` use it instead
  of their improvised tests, and `statement-suspect` reports cite its record.

Depends on `step-records`.

## Capabilities

### New Capabilities

- `certificates/meaning-check`: the command, the step, its outcomes and its record.

### Modified Capabilities

None.

## Impact

- Lean: `Veriphy/Tactic/Meaning.lean` (the command, reusing `sage_test`'s binder opening and problem serialization).
- Python: a daemon method `meaning` in `veriphy.oracle`, using the toolkit's seeded `Sampler` and exact or interval
  evaluation, and the `meaning` step.
- Playbooks: `prove.md` step 1, `research/triage.md`.
