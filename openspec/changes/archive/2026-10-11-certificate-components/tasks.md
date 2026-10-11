# Tasks

## 0. Baseline

- [x] 0.1 Commit or stash the current uncommitted work (`Veriphy/Tactic/SageExists.lean`, `SageFarkas.lean`, and the server and Bridge changes) so the refactor starts from a known-green tree. Verify that `lake build` and `lake build VeriphyTest` both pass, and record the output.

## 1. Python method framework (oracle-methods)

- [x] 1.1 Add `ParamError`, the coercers (`Vars`, `Poly`, `PolyList`, `RelList`, `Str`, `Int`) and `encode()` (QQ to string, polynomial to term list, recursive containers, reject floats when not advisory) to `sage_bridge/server.py`. Verify with the new `sage_bridge/test_server.py` cases for encoding and for each coercer's error naming its parameter.
- [x] 1.2 Add the `@method(name, advisory=False, **params)` decorator that registers in `METHODS` and wraps errors as `"<method>: <reason>"`. Make `main()` report unknown methods by name. Verify with a unittest that sends an unknown method and an invalid `vars`, and a manual `echo '{"id":1,"method":"ping"}' | sage -python sage_bridge/server.py` that shows an unchanged response.
- [x] 1.3 Add the `exact_lp(nvars, eqs, les, objective, nonneg)` helper with guards for zero variables and zero constraints and `None` on infeasibility. Verify with unittests for the empty, infeasible (`t ≤ 0`, `t ≥ 1`) and fractional-solution (`"1/3"`) cases.
- [x] 1.4 Migrate `factor`, `sos` (hints path onto `exact_lp`), `roots`, `lincomb`, `farkas` (onto `exact_lp`), `exists` (onto `exact_lp`) and `sum` to the decorator. Verify that their parameter names and result shapes are unchanged with one unittest per method on the existing `VeriphyTest.lean` inputs.
- [x] 1.5 Migrate `symbolic_check`, `matrix_check`, `solve` and `run_script` with `advisory=True`, factoring `run_script`'s exec, preparse, stdout and timeout code into `_run_sage(script, ns, timeout)`. Verify with unittests that `run_script` still returns `results`, `stdout` and `advisory`.

## 2. Lean kit: extraction and builders

- [x] 2.1 Create `Veriphy/Kit/Build.lean` by moving `parseRat`, `ratStx`, `ratStx'`, `termStx` and `polyStx` from `Translate.lean`, and make `Translate.lean` import it. Verify that `lake build` passes with no edits to the tactic files.
- [x] 2.2 Add `weightedSum` (drops zeros, errors on empty), `witness` (checks arity), `steps` and `freshIdent` (an unused local name with no macro scopes) to `Kit/Build.lean`. Verify with `#eval`/`example` checks in a new `VeriphyTest/Kit.lean` section (no Sage needed) that the printed output has no `✝` and that the errors fire.
- [x] 2.3 Create `Veriphy/Kit/Problem.lean` with `Rel`, `relOf?` (with the ≥/> flips and `¬ =` as `≠`), `Constraint`, `Goal`, `Problem`, `ProblemM` and `tryTranslate`. Verify with Sage-free tests that extract `x ≥ 2` as `2 - x ≤ 0` and `¬ (v = 0)` as `ne`.
- [x] 2.4 Implement `extract` (hypothesis collection over the carrier with rollback, exclusion of inaccessible names, goal classification, existential peeling, conjunct splitting, the free-atom check) and `Problem.toJson`. Verify with Sage-free tests for: a shared atom between goal and hypothesis, a skipped untranslatable hypothesis, a skipped `h✝`, a two-binder `∃` with three conjuncts, the free-parameter error, and the JSON fields.

## 3. Lean kit: bridge call, families, replay

- [x] 3.1 Add `Bridge.call` with a decoder to `Veriphy/Bridge.lean` and rewrite the existing `Bridge.*` functions over it, keeping their signatures. Add `Kit.call` in `CoreM`, which refuses when `veriphy.internal.replaying` is set. Verify that `lake build` passes and that `#sage_factor "x^4 - 1" "x"` prints the same certificate as before.
- [x] 3.2 Create `Veriphy/Kit/Replay.lean` with the `veriphy.checkReplay` and `veriphy.internal.replaying` options and the replay procedure (print, parse, restore, run with the bridge disabled, compare goals, restore). Verify with a test that a hand-built proof containing a hygienic ident fails replay with its printed text, and that a good proof passes and leaves identical goals and messages.
- [x] 3.3 Create `Veriphy/Kit/Family.lean` with `closeAndEmit` (run what you print, then optional replay, then one `Sage-free replacement:` suggestion) and the five families: `identity` (rewrite and lincomb forms), `inequality` (direct and refutation forms), `witness`, `sum` and `cases`. Verify with Sage-free examples that feed literal certificates into each family, including the failing cases (wrong cofactors, a negative weight) under `fail_if_success`.
- [x] 3.4 Add `Veriphy/Kit.lean` re-exporting the kit, import it from `Veriphy.lean`, and add `VeriphyTest/Kit.lean` (or a Sage-free section) to the test library. Verify that `lake build` and `lake build VeriphyTest` pass.

## 4. Migrate the existing tactics (one per task, replay on)

- [x] 4.1 Add `set_option veriphy.checkReplay true` to the top of `VeriphyTest.lean`. Verify that the file still builds (it should, because unmigrated tactics do not go through `closeAndEmit` yet).
- [x] 4.2 Migrate `sage_lincomb` to `extract`, `Kit.call` and the identity family. Verify that `lake build VeriphyTest` passes and add the regression for an inaccessible hypothesis (`intro` of an unnamed hypothesis, then `sage_lincomb`).
- [x] 4.3 Migrate `sage_farkas` to the inequality family's refutation form. Verify that `lake build VeriphyTest` passes, including the existing `u ≤ 0` negation example, and add a regression with only equality hypotheses (the empty-LP case).
- [x] 4.4 Migrate `sage_factor` to the identity rewrite form ("run what you print"). Verify that the five existing `sage_factor` examples pass with replay.
- [x] 4.5 Migrate `sage_sos` (plain and hinted) to the inequality family. Settle the printed form (design Open Question 1) and verify that every existing `sage_sos` example passes with replay.
- [x] 4.6 Migrate `sage_witness` and `sage_exists` to the witness family. Verify that the existing examples pass and add the regression for `∃ x y : ℚ, x = y` (no inequalities, so no LP).
- [x] 4.7 Route `sage_sum`'s proof through the sum family, keeping its macro syntax. Verify that both `sage_sum` examples pass and that `#sage_sum "k^2"` output is unchanged.
- [x] 4.8 Grep `Veriphy/Tactic/` for direct `Bridge.` calls (other than `#` commands), `IO.mkRef`, and bare idents inside tactic quotations. Verify that the grep is empty and that each tactic file is about 40 lines or fewer.

## 5. Agent route: `sage_certify`

- [x] 5.1 Add the `certify` daemon method: pre-bind `R`, the generators, `hyps`, `goal`, `binders` and `atoms`; run via `_run_sage`; validate and normalize the per-family schema; include truncated stdout on errors. Verify with unittests for a well-formed inequality certificate, a missing `certificate`, an unknown hypothesis name, the wrong witness arity, and a script that raises `ZeroDivisionError`.
- [x] 5.2 Add `Bridge.certify` and `Veriphy/Tactic/SageCertify.lean` with the `sage_certify (identity|inequality|witness) "<script>"` syntax, a goal-shape check before any Sage call, reconstruction and the family close. Import it in `Veriphy.lean`. Verify that `lake build` passes.
- [x] 5.3 Add `sage_certify` tests to `VeriphyTest.lean`:
  - identity on `a ^ 2 + b ^ 2 = 5`;
  - inequality on `a * b ≤ (a ^ 2 + b ^ 2) / 2` with the square `(1/2, a - b)`;
  - inequality refuting `False` from linear hypotheses;
  - witness on the eigenvector goal;
  - under `fail_if_success`: a family/goal mismatch, bad weights, and a wrong-arity witness.

  Verify that `lake build VeriphyTest` passes with replay on, and that the emitted suggestions contain no script text.

## 6. Documentation

- [x] 6.1 Update `prompts/prove.md` step 3. Add a `sage_certify` sub-step between the dedicated tactics (3c) and the advisory oracle (3d), with the three families and the pre-bound names. Narrow `blocked-missing-tactic` in step 5 to "no checker family can verify it". Verify by reading the result against the agent-certify spec's last requirement.
- [x] 6.2 Update `docs/DESIGN.md`. In §4, the catalog grows by families and agent certificates. Add a short "Adding a certificate" subsection covering the six stages and which kit pieces cover each, with a minimal example tactic. Verify that the example in the doc compiles by pasting it into a scratch file under `lake env lean`.
- [x] 6.3 Update `README.md` (add a `sage_certify` row to the tactic table and mention `veriphy.checkReplay` for contributors) and `skills/prove/SKILL.md` if it lists tactics. Verify that the test command for `sage_bridge/test_server.py` is documented and runs as written.

## 7. Integration check

- [x] 7.1 With Sage on `PATH`, run `lake build`, `lake build VeriphyTest` and `sage -python -m unittest sage_bridge/test_server.py`, all green. Then, with Sage removed from `PATH`, paste every emitted `Try this:` replacement from `VeriphyTest.lean` into a scratch file and verify that it builds (end-to-end confirmation that it is Sage-free).
- [x] 7.2 Run `openspec validate certificate-components --strict` and verify that it passes.

## Workflow follow-up

- Archive the change with `/opsx:archive` after review, then verify that `openspec/specs/certificates/*` holds the six new capability specs.
