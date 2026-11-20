# Proposal

## Why

Claims are layer 2: what the records establish. Today the levels are fixed in three places (`vocabulary.ttl`,
`_vocabulary.LEVELS` and Lean's `levelOf`), all mathematical, and nothing checks that a level was granted by a tool
that can grant it. A claim's own level comes only from a Lean export. For other fields to fit, levels must come from
packs, every level must belong to a trust class, and any step's record must be able to give a claim its level.

## What Changes

- **Trust classes are fixed.** `kernel`, `checker`, `reproduction`, `oracle`, `measurement` and `search`, in the
  schema, not configurable. `measurement` and `search` grant no level.
- **Levels come from packs.** Each level names its trust class and the level directly below it, and the levels of a
  workspace form one order. `core` declares `none`, `lean` declares `lean-proof`, and `math` declares `certificate`,
  `kernel-test` and `oracle-test`, giving today's five levels in today's order.
- **The grant rule.** A step grants only levels of its primitive's trust class, checked by `config check` and again
  when a record is written.
- **Claims from any record.** A claim's own level is the highest level granted by a record linked to it, a Lean
  export included. Effective levels and their caps work as before over the configured order.
- **The vocabulary follows the config.** The graph's level individuals and their order are generated from the resolved
  config, and reports name the trust class beside every level.
- **Claims without Lean.** With `packs: [core]`, the claim graph, reasoning and reports work, with `none` and whatever
  levels the other selected packs add.

Depends on `declarative-steps`.

## Capabilities

### New Capabilities

- `core/trust`: trust classes, levels from packs, one order, the grant rule and class-qualified reports.

### Modified Capabilities

- `certificates/test-fallback`: the five levels are declared by the `lean` and `math` packs, each with its class.
- `research/claim-graph`: the vocabulary's levels come from the resolved config.
- `research/effective-levels`: a claim's own level comes from any record linked to it, and the report names classes.

## Impact

- `veriphy.graph`: levels, the vocabulary and the report read the claims registry.
- `veriphy.steps`: the runner checks the grant rule before writing a record.
- Packs: `levels` in `core`, `lean` and `math`.
- Lean: a test keeps `#veriphy_levels`'s names equal to the `lean` and `math` packs' levels.
