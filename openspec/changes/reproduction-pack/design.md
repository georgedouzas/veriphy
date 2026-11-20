# Design

## Context

After `tool-contracts`, a tool is YAML: a command, a contract and a pin. The claim graph already carries conventions,
`excludes` and effective levels, and `oo-horn` checks the reasoning whatever the levels are called.

## Goals / Non-Goals

**Goals:**

- Show that a new field needs YAML, a playbook and no change to the core.
- Make `reproduced` mean one exact thing: the same estimate from the same code, data and environment.

**Non-Goals:**

- Judging whether an analysis is correct. A reproduced estimate can still be a bad estimate.
- Support for Stata or SAS, which are licensed. The pack shows the pattern with R.

## Decisions

### D1. Data is pinned by content

The claim names its data by SHA-256. `reproduce` refuses to run when the file's hash differs, so a reproduction is
always of the data the claim names.

### D2. The script reports a named estimate

The analysis script writes `{"estimate": …, "se": …}` to `{out}`. The step compares `estimate` with the claim's value
within the declared tolerance and records both values in every outcome.

### D3. Robustness is a declared list

The variations (other controls, another period) are listed with the claim before `test` runs, so an agent cannot pick
variations after seeing results. `robust` requires the estimate's sign and significance to hold under each.

### D4. Identification is a convention

`identification` is a convention aspect with `parallel-trends` and `no-parallel-trends`. A claim that rests on one and
cites a claim that assumes the other is a clash, found by the existing graph checks.

## Risks / Trade-offs

- [A container runtime is needed] → The pack's tests skip without one, and CI runs them.
- [`robust` depends on the chosen variations] → The record lists them, and the report shows them beside the level.
