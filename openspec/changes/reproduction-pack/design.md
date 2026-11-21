# Design

## Context

After `claims-and-trust`, a pack can add tools, primitives, steps with `compare`, levels with a trust class, and
conventions, and the claim graph takes own levels from any record. The graph already finds clashes between exclusive
conventions, and `oo-horn` checks the reasoning whatever the levels are called.

## Goals / Non-Goals

**Goals:**

- Show that a new field fills every layer with YAML, one small composite, a playbook, and no change to the core.
- Make `reproduced` mean one exact thing: the same estimate from the same code, data and environment.

**Non-Goals:**

- Judging whether an analysis is correct. A reproduced estimate can still be a bad estimate.
- Support for Stata or SAS, which are licensed. The pack shows the pattern with R.

## Decisions

### D1. Data is pinned by content, in the primitive

`r.run`'s input names the data file and its expected SHA-256, and the primitive refuses to start R when they differ.
So a reproduction is always of the data the claim names, whoever calls the primitive.

### D2. The script reports a named estimate

The analysis script writes `{"estimate": …, "se": …}` to `{out}`. The `reproduce` step compares `estimate` with the
claim's value by the generic `compare`, and records both values in every outcome.

### D3. Vary is a declared list, run by a composite

The variations (other controls, another period) are listed with the claim before `vary` runs, so an agent cannot
pick variations after seeing results. `r.vary` runs `r.run` once per variation, and its output says whether the
estimate's sign and significance hold under each. Its deciding part is `r.run`, so its class is `reproduction`.

### D4. Identification is a convention

`identification` is a convention aspect with `parallel-trends` and `no-parallel-trends`. A claim that rests on one and
cites a claim that assumes the other is a clash, found by the existing graph checks.

### D5. No Lean, by test

The pack's tests run with `packs: [core, reproduction]`, so any hidden dependency on Lean or SageMath fails them.

## Risks / Trade-offs

- [A container runtime is needed] → The pack's tests skip without one, and CI runs them.
- [`robust` depends on the chosen variations] → The record lists them, and the report shows them beside the level.
