# Design

## Context

`vocabulary.ttl` states five level individuals and their order, `_vocabulary.LEVELS` repeats them, and Lean's
`levelOf` computes them from proof terms. Effective levels take the minimum of a claim's own level and its
dependencies' effective levels, and `oo-horn` checks that reasoning. After `declarative-steps`, check and derived
steps declare `grants`, and nothing yet checks it.

## Goals / Non-Goals

**Goals:**

- A field adds levels without touching the core, and they compose with other fields' levels in one order.
- No configuration can make a heuristic grant proof-like trust.

**Non-Goals:**

- Partial orders of levels. One order keeps effective levels a minimum, which `oo-horn` already checks.
- Changing how Lean computes its levels. `#veriphy level` keeps computing them, and the packs declare their names.

## Decisions

### D1. Six fixed classes

The classes are part of the schema. A pack can add tools, primitives, steps and levels, but cannot add a class, so
`kernel` and `checker` always mean a proof or certificate checked by a trusted checker.

### D2. One order, settled by the workspace

Each level names the level directly below it (`above`). `config check` requires one chain from `none`. When two
unrelated packs place a level in the same position (say `reproduced` and `oracle-test`, both above `none`), it names
both, and the workspace file states the order by overriding the `above` of the levels concerned. This is the collision
rule of `packs-and-config` applied to positions.

### D3. The grant rule is checked twice

`config check` refuses a step whose `grants` names a level of another class than its primitive's. The runner checks
again before writing a record, so a record never carries a level its primitive could not grant, whatever the config.
Derived steps grant the class of the primitive they derive from: `level` reads `lean.level`, which is `kernel`.

### D4. Own levels from records

A claim's own level is the highest level of any record linked to it: a record whose inputs name the claim, or name
the Lean declaration that formalizes it. The Lean export becomes one such record. This keeps reports functions of
records, and lets a reproduction record give an economic claim its level.

### D5. Classes travel with levels

Every report shows the class beside the level, as `reproduced (reproduction)` or `certificate (kernel)`, so a reader
never mistakes a reproduction or an oracle test for a proof.

## Risks / Trade-offs

- [Three sources of Lean level names: Lean, the packs, old graphs] → A test keeps the packs equal to
  `#veriphy level`, and graphs written before this change load, since the names do not change.
- [Workspaces combining fields must order levels] → Only when two packs claim the same position, and the error names
  the key to set.

