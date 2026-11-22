# Proposal

## Why

Subfield packs sat beside their fields in `veriphy/packs/`, joined to them only by `requires`, so the package tree
did not show which field a pack belongs to. Mathematics had no subfields at all, though Sage ships the libraries its
subfields trust: PARI for number theory, GAP for group theory, its own graph library for graph theory.

## What Changes

- A subfield's pack is nested in its field's pack, and builds on it without naming it in `requires`: built-in packs
  by package (`veriphy.packs.physics.particle_physics`), local packs by directory.
- **BREAKING** The subfield packages move: `particle_physics` and `general_relativity` into `physics`, `genomics`
  into `life_sciences`, `econometrics` into `economics`, `epidemiology` into `statistics`. Pack names are unchanged.
- New subfields of `math`: `number-theory` (factorizations with proven primality, certified class numbers, with
  PARI), `group-theory` (finite groups, with GAP) and `graph-theory` (graph invariants, with Sage). Each grants
  `oracle-test`.
- The math pack's `sage` tool runs a pack's own function under Sage with `run <module:function>`, so a subfield keeps
  its code in its own package.
- Yes-or-no properties are refused in words: "it is not abelian".

## Capabilities

### New Capabilities

- `packs/number-theory`, `packs/group-theory`, `packs/graph-theory`: the subfields of mathematics.

### Modified Capabilities

- `core/workspace-config`: nested packs build on the pack around them.
