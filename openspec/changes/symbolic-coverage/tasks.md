# Tasks

## 1. Baseline measurement (translation-coverage)

- [ ] 1.1 Add `Veriphy/Kit/Coverage.lean` with `#veriphy_coverage [prefixes] "out.json"` (D7). It classifies atoms as local, uninterpreted or opaque, counts per statement and per head, and writes JSON plus a summary. Verify with Sage-free `#guard_msgs` tests in `VeriphyTest/Kit.lean` on a small local namespace, covering a fully covered statement, one with `Real.Gamma`, one with an uninterpreted `f x`, and one with no relation.
- [ ] 1.2 Create the `coverage/` runner project: `require veriphy from ".."`, Physlib at a commit whose mathlib pin matches Veriphy's, and `Archive` from mathlib, plus `Coverage.lean` running the command on both corpora. Verify that `lake build` in `coverage/` produces two JSON reports.
- [ ] 1.3 Record the baseline in `docs/development/coverage.md`: corpus revisions, date, the three numbers per corpus and the top 30 opaque heads. Verify that the page builds with `nox -s docs -- build`.

## 2. Table format and generalized conditions (symbolic-translation, translation-extensions)

- [ ] 2.1 Turn the core function table into data records (D1), and add the mirrored `core_table.json` in the Python package. Verify with a Sage-free Lean test that the two agree, and that all existing kit and round-trip tests stay green.
- [ ] 2.2 Add the `le` condition kind with two terms and constant bounds (D3), including discharge by `b < a`. Verify with kit tests for `k ≤ n` discharged by `hk : k ≤ n` and by `hk : k < n`, and an undischarged one.
- [ ] 2.3 Add `typed` sub-expressions to `SymExpr` and their serialization (D5). Verify with kit tests showing `typed(mod(x0, 7), 'ℕ')` for `((n % 7 : ℕ) : ℝ)`, and no marker inside a pure ℕ goal.

## 3. Core coverage (symbolic-translation)

- [ ] 3.1 Functions: `rpow`, `cosh`, `sinh`, `tanh`, `arctan`, `arcsin`, `arccos`, `Real.logb`, each with its conditions (D4). Verify with one kit test per function, showing its form and conditions.
- [ ] 3.2 Sums and products over `Icc`, `Ico` and `range` with symbolic bounds, nested. Verify with kit tests, including a nested double sum.
- [ ] 3.3 Integer functions and integer `/`, `%` and ℕ subtraction with the gap rules (D4). Verify with kit tests: `n / 2` translated, `n / m` opaque without `0 < m`, `n - k` opaque without `k ≤ n` and translated with it.
- [ ] 3.4 `deriv` of covered bodies at covered points, with conditions at the point (D4). Verify with kit tests for `deriv (fun x => x ^ 2 * Real.exp x) 1` and `deriv (fun x => Real.log x) a`, the second listing `a ≠ 0`.

## 4. Rendering and emitters (symbolic-emitters)

- [ ] 4.1 Bind `extensions` and `typed` in `read_problem`, and parse `typed` as the identity while recording marked sub-expressions. Verify with pytest on serialized problems containing each.
- [ ] 4.2 Extend the rendering table to the new functions, and make rendering type-aware (D5), with a `type=` parameter and outermost ascription. Verify with pytest for each new function, for `((n % 7 : ℕ) : ℝ) + x`, and for rendering at ℕ, plus the Lean parse check.
- [ ] 4.3 Add the shared rewrite table (core entries and project entries) and `rewrite_candidates(problem)`, and move `transcendental_rewrite`'s table onto it. Verify with pytest selecting `Real.log_mul` with its side conditions, and with the recipe's existing examples still passing.
- [ ] 4.4 Add `has_deriv_at` (D6). Verify with doctests, a pytest failure naming an undischarged `a ≠ 0`, and the Lean parse check.
- [ ] 4.5 Extend the round-trip suite in `VeriphyTest/SageRun.lean` with one example per new construct. Verify that `lake env lean VeriphyTest/SageRun.lean` passes with replay on.

## 5. Project translation tables (translation-extensions)

- [ ] 5.1 Load, validate and merge `translations/*.json` in Lean (D2): schema errors naming the file and field, conflicts naming both entries, a per-process cache, and serialization of the entries the problem uses. Verify with kit tests using a fixture directory with a valid entry, an invalid one and a conflicting one.
- [ ] 5.2 Add `veriphy.translations` (`list`, `show`, schema validation shared with the toolkit). Verify with pytest on the fixture directory and a run of `sage -python -m veriphy.translations list`.
- [ ] 5.3 Add the round-trip check command for project entries, covering function and rewrite entries. Verify on the fixture directory: valid entries pass, and one with a wrong Sage name fails with its error.
- [ ] 5.4 Add the "unknown function" step to `prompts/certify.md` and the `certify` skill, and an example entry (`Real.arcosh`) in the user guide. Verify with a scratch project where `Real.arcosh` is opaque until the entry is added and checked, and is then translated.

## 6. Recipes (procedures)

- [ ] 6.1 Write the `derivative` recipe and template. Verify that its worked example passes in `VeriphyTest/SageRun.lean` with replay on, and that the recipe-template pytest check passes.
- [ ] 6.2 Extend `sum_induction` to `Icc`/`Ico` sums. Verify with `∑ k ∈ Finset.Icc 1 n, (k : ℚ) = n * (n + 1) / 2` in the Lean suite.
- [ ] 6.3 Verify that `transcendental_rewrite` selects a project rewrite entry (`Real.cosh_sq` from a fixture) without edits, in a scratch project.

## 7. Measurement after, docs and integration

- [ ] 7.1 Rerun the coverage runner and record the post-change numbers and classified top heads in `docs/development/coverage.md`. Verify that the fully covered share is at least the baseline's for both corpora, and that every listed head is classified.
- [ ] 7.2 Update the user guide (project tables, typed rendering), the developer guide (adding a core entry, running coverage), the README coverage paragraph and the recipe index. Verify that `nox -s docs -- build` succeeds.
- [ ] 7.3 Run `nox -s checks`, `nox -s tests`, `lake build VeriphyTest` and the replay of every replacement with Sage off `PATH`, all green. Push the branch and verify that CI is green.
- [ ] 7.4 Run `openspec validate symbolic-coverage --strict` and verify that it passes.

## Workflow follow-up

- Archive the change and merge to `main`.
- Release 0.2.0 through the release flow, once PyPI trusted publishing is configured.
