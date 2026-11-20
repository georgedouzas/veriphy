# Proposal

## Why

The architecture claims that a field with no proofs fits the same layers: its own primitives, steps, levels,
conventions, workflow and playbook, with the core unchanged and no Lean. That claim needs a working pack outside
mathematics before anything else relies on it. Reproducing a published statistical result is the clearest case: an
empirical claim, a tool that is not Sage, and a level that is not a proof.

## What Changes

A pack, `reproduction`, shipped with Veriphy, requiring only `core`, and adding to every layer:

- **Primitives:** an `r` tool (files contract, pinned by container image), `r.run` (class `reproduction`), which runs
  an analysis script on data whose SHA-256 it checks, with a seed, and the composite `r.robustness`, which runs
  declared variations.
- **Steps:** `reproduce`, declared in YAML over `r.run` with `compare` against the claimed estimate, granting
  `reproduced`; and `robustness` over `r.robustness`, granting `robust`.
- **Claims:** the levels `reproduced` and `robust` of class `reproduction`, and the convention aspect
  `identification` with `parallel-trends` and `no-parallel-trends`.
- **Workflow:** `reproduce-analysis`.
- **Agents:** a `reproduce` playbook and skill.
- A worked example: a small public dataset, a regression script and a claim, used by the tests and the docs.

Depends on `claims-and-trust`. The workflow entry is accepted as data now, and runs once `workflows-as-data`
lands.

## Capabilities

### New Capabilities

- `packs/reproduction`: the pack, its primitives, steps, levels, convention, workflow and playbook.

### Modified Capabilities

None.

## Impact

- New: `veriphy/packs/reproduction/` (pack.yaml, schemas, the composite's module, playbook, example),
  `skills/reproduce/`.
- CI: a job that runs the example in the pinned R image.
