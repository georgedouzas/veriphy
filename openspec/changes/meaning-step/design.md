# Design

## Context

`sage_test` already opens a claim's universal binders, serializes the problem, and evaluates oracle instances in exact
or interval arithmetic of at least 53 bits. The toolkit's `Sampler` draws seeded rationals and matrices, and
`default_cases` picks values by binder type. `symbolic_check` decides identities under assumptions.

## Goals / Non-Goals

**Goals:**

- A seeded, recorded test of a statement, the same every time it runs on the same declaration.
- A counterexample that a person can read and Lean could restate.

**Non-Goals:**

- Checking the informal side. The back-translation stays the agent's, and the record stores the agent's text.
- Granting a level. A statement that agrees at every value is still not proved.

## Decisions

### D1. Built from `sage_test`'s parts, with no user script

The command reuses binder opening and serialization, and the daemon method draws the values itself from
`default_cases` with the seed. No script is needed, so the step is the same for every claim.

### D2. Hypotheses by rejection

Values are drawn and kept only when every hypothesis evaluates to true. When fewer than 10 values survive 200 draws,
the outcome is `undecided` and names the hypothesis that rejected most, so the agent can supply values.

### D3. Exact first, intervals second

Each kept value is evaluated exactly when Sage can, otherwise in interval arithmetic of at least 53 bits. An interval
that contains both outcomes counts as undecided for that value, never as agreement.

### D4. Identities ask `symbolic_check` first

When the statement is an equation, `symbolic_check` runs under the hypotheses. `equal: true` is recorded as
symbolic agreement, `equal: false` with its witness as a counterexample, and `null` falls back to sampling.

### D5. The agent's back-translation is an input

`--informal "<text>"` stores the agent's English reading in the record, so the record shows what was compared, and the
digest changes when the reading does.

## Risks / Trade-offs

- [Rejection sampling fails on narrow hypotheses] → `undecided` names the hypothesis, and `--values` lets the agent
  give values, which are recorded.
- [Agreement read as proof] → The record has kind `evidence` and no level, and reports say `agrees at n values`.
