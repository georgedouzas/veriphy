# Design

## Context

`levelOf` in `Veriphy/Kit/Levels.lean` reads the `veriphy_tested` attribute, then looks for `Veriphy.certified` in the
proof term, and otherwise returns `none`. `Veriphy/Kit/Family.lean` already rejects a recipe's block on axioms outside
`standardAxioms`, but nothing checks a theorem's axioms when its level is reported.

## Goals / Non-Goals

**Goals:**

- A complete proof ranks above any test, and a theorem with no complete proof ranks at `none`.
- The level comes from the Lean environment alone, as the export spec requires.

**Non-Goals:**

- Changing how `sage_test` records a test.

## Decisions

### D1. Certificate ranks above lean-proof

Both are kernel-checked, so `certificate` is not logically stronger. It stays on top because a recipe also leaves a
reusable script, and because a certificate capped by a plain lemma should say which lemma. No report calls a claim
proved below `lean-proof`, so this order does not weaken what `proved` means.

### D2. Axioms come from `collectAxioms`

`levelOf` calls Lean's `collectAxioms`, which follows the whole dependency closure, so a `sorry` in a lemma reaches the
theorem that uses it. Measured on 500 `Real.*` theorems of mathlib, it adds 165 ms in total, so no cache is needed.

### D3. A recorded test keeps its level

`veriphy_tested` is read first, as today, so a tested theorem reports its test level. See the open question.

## Risks / Trade-offs

- [Effective levels rise in existing graphs after a new export] → That is the correction this change makes, and the
  level report names the level of every claim.

## Open Questions

- A theorem with a complete proof reports `lean-proof`, and adding `sage_test` to it lowers it to `kernel-test` by D3.
  This keeps the specified behaviour of tested claims. Whether a complete proof should win is left for a later decision.
