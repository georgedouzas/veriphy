# Tasks

## 0. Prerequisite

- [ ] 0.1 Confirm that `sage-building-blocks` is archived and merged to `main`, and branch `symbolic-translation`. Verify with `git log` and a green `main`.

## 1. Lean translation (symbolic-translation)

- [x] 1.1 Add `SymExpr` and its rendering to Sage syntax (D1). Verify with `#guard_msgs` tests rendering one term per constructor.
- [x] 1.2 Port the coverage tables from LeanSage (D2), with attribution, and implement `exprToSym` for the coverage list, with typed atoms. Verify with Sage-free tests, one per covered construct, including `abs` over ℝ, ℂ and ℤ.
- [x] 1.3 Collect domain conditions and match them to hypotheses (D3). Verify with tests for a discharged denominator, an undischarged `log` argument, and a `sqrt` argument discharged by `0 ≤ u`.
- [x] 1.4 Serialize `expr`, atom types and domain conditions in `Problem.toJson`. Verify by updating the kit's lenient-extraction expectations.

## 2. Python binding and emitters (symbolic-emitters)

- [x] 2.1 Bind `Hyp.expr`, `Problem.atom_types` and `Problem.domain` (D4). Verify with pytest on serialized problems containing each kind.
- [x] 2.2 Implement `symbolic`, `matrix_term`, `field_simp_clearing` and `lemma_rewrite` (D5), each with a doctest and a Lean parse check. Verify that the function-table, `abs` dispatch and unmapped-function tests pass.
- [x] 2.3 Add round-trip tests (D6): one Lean example per covered construct, translated and rendered back, then proved equal. Verify that all pass.

## 3. Recipes

- [ ] 3.1 Write the `rational_inequality`, `transcendental_rewrite` and `matrix_from_goal` recipes, each with a tested template. Verify that their worked examples (including `x / (x ^ 2 + 1) ≤ 1 / 2` and `Real.exp a * Real.exp b = Real.exp (a + b)`) pass in `VeriphyTest/SageRun.lean` with replay on, and that the recipe-template pytest check passes.
- [ ] 3.2 Add the new recipes to the index in `prompts/prove.md` and to `prompts/certify.md`'s toolkit list, and credit LeanSage in the README and the user guide. Verify that the docs build.

## 4. Integration

- [ ] 4.1 Run `nox -s checks`, `nox -s tests` and `lake build VeriphyTest`, all green, with the benchmark unchanged.
- [ ] 4.2 Run `openspec validate symbolic-translation --strict` and verify that it passes.
