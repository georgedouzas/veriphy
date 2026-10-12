# Tasks

## 0. Prerequisite

- [ ] 0.1 Confirm that `package-and-distribute` is merged to `main` and that `main` is green (`nox -s checks`, `nox -s tests`, `lake build VeriphyTest`). Branch `sage-building-blocks` from it. Verify with `git log` showing the merge and the three commands passing.

## 1. Toolkit foundation (lean-emitters, search-primitives)

- [ ] 1.1 Create `src/veriphy/toolkit/` with `Problem` and `Hyp` (moved from `oracle/_scripts.py`, widened with Lean text and optional polynomial forms), and re-export them. Verify with pytest cases that bind a problem containing a non-polynomial hypothesis, and with the existing certify tests staying green.
- [ ] 1.2 Add `toolkit/_lean.py`: the `Lean` value (text and kind) and rendering of rationals and polynomials over atoms (compound atoms parenthesized). Verify with doctests, plus a pytest fixture that parses emitted text with `lake env lean` (term and tactic categories).
- [ ] 1.3 Add `toolkit/_emit.py` builders:
  - hypothesis references (rejecting unknown names);
  - `linear_combination`;
  - `sq_nonneg`/`mul_nonneg`/`mul_pos`;
  - `nlinarith`/`positivity`/`field_simp`/`norm_num` with hints;
  - `rw [show … by …]`;
  - `calc`;
  - `by_cases`/`rcases` splits;
  - witnesses;
  - step sequences;
  - fresh names.

  Verify with a doctest per builder and the parse fixture on each builder's output. The output must contain no `✝`.
- [ ] 1.4 Move the exact LP, cofactors, factorization and Farkas search into `toolkit/_algebra.py`, and add normal forms and substitutions. The oracle methods become wrappers. Verify that the existing oracle tests pass unchanged and that each primitive has a doctest.
- [ ] 1.5 Move rational points and roots into `toolkit/_structure.py`, and add real-root isolation with rational separating points, sign/case enumeration and matrix decompositions. Verify with tests, including isolating `x^2 - 2`, a similarity transform checked by exact multiplication, and a kernel basis.

## 2. Positivity search (search-primitives)

- [ ] 2.1 Implement the `nlinarith` product search (D6), with caps and an optional `linear_combination` output. Verify with tests on `a*b ≤ (a^2+b^2)/2`, on an inequality that needs a product of two hypotheses, and on an infeasible case that reports "no product certificate".
- [ ] 2.2 Implement SOS: the factor-based and hinted routes (moved), plus the SDP route with rounding, exact projection and an LDLᵀ check (D7). Verify on the existing SOS inputs, on an irreducible quartic found only through the SDP, and with a test showing that a perturbed problem reports failure instead of an inexact result.

## 3. Script tactic (script-tactic)

- [ ] 3.1 Add the daemon method `run` (`script` or `preset`, `args`, `timeout_s`), which returns `{lean, stdout}`, binds the problem and toolkit, and resets symbolic state after each request. Verify with pytest: a script that assigns `proof`, a missing `proof`, a script that raises (stdout included), and a no-leak test for `assume`.
- [ ] 3.2 Add the lenient extraction mode to `Veriphy/Kit/Problem.lean` (D2): every goal kind, and every nameable hypothesis with its text and an optional polynomial. Verify with Sage-free `#guard_msgs` tests in `VeriphyTest/Kit.lean` for a goal with `Real.sin` and a hypothesis that does not translate.
- [ ] 3.3 Add the axiom guard to `closeAndEmit` (D3). Verify with Sage-free kit tests: a block using `sorry` is rejected with `sorryAx` named, `native_decide` is rejected with `Lean.ofReduceBool` named, a `decide` proof is accepted, and the existing kit tests stay green.
- [ ] 3.4 Add `Veriphy/Tactic/SageRun.lean`: parse the returned text, run it through `closeAndEmit`, and produce the three-section combined error. Verify in `VeriphyTest.lean` with replay on:
  - a hint example, a `calc` derivation, a case split, a witness with a `norm_num` side goal, a matrix identity, and a rewrite step that leaves a residual goal;
  - failing examples under `fail_if_success` with their messages checked by `#guard_msgs`: an unparseable block, a wrong hint, a script that raises, and `sorry`.

## 4. Persistent session (daemon-session)

- [ ] 4.1 Replace spawn-per-request in `Veriphy/Bridge.lean` with a session: one process per Lean process, a mutex, matched request ids, a timeout that kills the process, and a single retry on EOF (D9). Verify with a file running ten `sage_*` calls whose timing shows one start-up, and with `lake build VeriphyTest` green.
- [ ] 4.2 Verify recovery and limits with scratch files:
  - killing the daemon between two calls (the second call succeeds);
  - a looping script (it fails after the limit, and the next call succeeds);
  - replay with a warm session (refused with the replay error).

## 5. Presets (checker-families modified)

- [ ] 5.1 Create `src/veriphy/presets/` with presets for `factor`, `sos`, `lincomb`, `witness`, `farkas` and `exists`, written on the toolkit, and `runPreset` on the Lean side. Migrate one tactic per commit, keeping `lake build VeriphyTest` green after each. Verify that the existing examples pass unchanged in their tactic calls and that the files under `Veriphy/Tactic/` shrink to preset calls.
- [ ] 5.2 Reimplement `sage_certify` as presets for its three families. Verify that its existing tests pass, including the mismatch and arity errors.
- [ ] 5.3 Remove kit builders that are no longer used. Verify with a grep for unused definitions and with `lake build`.

## 6. Agent workflow and docs (agent-certify modified)

- [ ] 6.1 Rewrite `prompts/prove.md` step 3 around the `sage_run` loop and the toolkit (D10), list the presets as shortcuts, and rename the report category to `blocked-missing-building-block`. Mirror this in `skills/prove/SKILL.md` and the README. Verify that `grep -rn blocked-missing-tactic` is empty outside `openspec/changes/archive`.
- [ ] 6.2 Add "Building proofs with sage_run" to `docs/overview/user_guide.md`, with the worked examples from 3.4, and toolkit authoring notes to `docs/development/index.md`. Verify that `nox -s docs -- build` succeeds and that every example in the docs is also a test in `VeriphyTest.lean`.

## 7. Integration

- [ ] 7.1 Run `uv run nox -s checks`, `uv run nox -s tests`, `lake build`, `lake build VeriphyTest` and `lake build VeriphyTest.Kit`, all green. Then build the replayed replacements of every `sage_run` example with Sage off `PATH`, which must succeed.
- [ ] 7.2 Run `openspec validate sage-building-blocks --strict` and verify that it passes.

## Workflow follow-up

- Release through the template's flow (tag `X.Y.Z`), then archive the change with `/opsx:archive`.
