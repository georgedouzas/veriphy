# Proposal

## Why

The architecture claims that a field with no proofs fits the same model: its own tools, levels and conventions, with
the core unchanged. That claim needs a working pack outside mathematics before anything else relies on it. Reproducing
a published statistical result is the clearest case: an empirical claim, a tool that is not Sage, and a level that is
not a proof.

## What Changes

- A pack, `reproduction`, shipped with Veriphy: an `r` tool (files contract, pinned by container image), the levels
  `reproduced` and `robust` of class `reproduction`, the convention aspect `identification`, and the workflow
  `reproduce-analysis`.
- Two steps: `reproduce` runs an analysis script on hashed data with a seed and compares the estimate with the claimed
  one within a tolerance. `test` runs declared variations and grants `robust` when the estimate holds under each.
- A playbook, `reproduce.md`, and a skill, `reproduce`, for agents.
- A worked example: a small public dataset, a regression script and a claim, used by the tests and the docs.

Depends on `tool-contracts`.

## Capabilities

### New Capabilities

- `packs/reproduction`: the pack, its steps, levels, conventions, workflow and playbook.

### Modified Capabilities

None.

## Impact

- New: `veriphy/packs/reproduction/` (pack.yaml, playbook, example), `skills/reproduce/`.
- CI: a job that runs the example in the pinned R image.
