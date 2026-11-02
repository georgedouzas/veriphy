# Proposal

## Why

`#veriphy_levels` gives a complete mathlib proof the level `none`, the same as a theorem that uses `sorry`. In a
research graph one plain lemma therefore caps everything that rests on it at `none`, although the kernel checked its
proof. The level `certificate` has the opposite gap: it only looks for the recipe marker, so a certified proof that
depends on `sorry` or an extra axiom still reports `certificate`.

## What Changes

- A new level `lean-proof`, between `kernel-test` and `certificate`: a complete Lean proof that no recipe built, on the
  standard axioms alone.
- `certificate` and `lean-proof` require the standard axioms. A theorem that depends on `sorry` or any other axiom has
  the level `none`, even with the recipe marker.
- The graph vocabulary, the Lean export, level reports and appendices carry the new level.
- The research playbook and skill stop calling a claim proved below `lean-proof`, where they said `certificate`.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `certificates/test-fallback`: five levels, and the level report rests on the axioms a proof uses.
- `research/claim-graph`: the vocabulary states five levels and their order.
- `research/lean-claim-export`: the export can carry `lean-proof`.

## Impact

- `Veriphy/Kit/Levels.lean` (`levelOf` now runs in a monad, to collect axioms), `Veriphy/Kit/Graph.lean`, and
  `Veriphy/Kit/Family.lean` (`standardAxioms` moves to `Levels`).
- `veriphy.graph._vocabulary` and `vocabulary.ttl`.
- Exports rewritten by `#veriphy_graph` report plain proofs as `lean-proof`, so effective levels in existing graphs can
  rise after a new export.
- `prompts/research.md`, both copies of the `research` skill, `prompts/recipes/test_fallback.md`, the user guide.
