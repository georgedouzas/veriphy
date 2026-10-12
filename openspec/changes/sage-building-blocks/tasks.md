# Tasks

## 0. Prerequisite

- [x] 0.1 Confirm that `package-and-distribute` is merged to `main` and that `main` is green (`nox -s checks`, `nox -s tests`, `lake build VeriphyTest`). Branch `sage-building-blocks` from it. Verify with `git log` showing the merge and the three commands passing.

## 1. Toolkit foundation (lean-emitters, search-primitives)

- [x] 1.1 Create `src/veriphy/toolkit/` with `Problem`, `Hyp`, `read_problem`, `create_ring` and `parse_polynomial` (moved from the oracle and widened with Lean text and optional polynomial forms). `RELATIONS` moves to `core`. Verify with doctests and pytest cases binding a problem with a non-polynomial hypothesis and an `other` goal, and with the existing suite staying green.
- [x] 1.2 Add `toolkit/_lean.py`: the `Lean` value (text and kind) and rendering of rationals and polynomials over atoms (compound atoms parenthesized). Verify with doctests, plus a pytest fixture that parses emitted text with `lake env lean` (term and tactic categories).
- [x] 1.3 Add `toolkit/_emit.py` builders:
  - hypothesis references (rejecting unknown names);
  - `linear_combination`;
  - `sq_nonneg`/`mul_nonneg`/`mul_pos`;
  - `nlinarith`/`positivity`/`field_simp`/`norm_num` with hints;
  - `rw [show … by …]`;
  - `calc`;
  - `by_cases`/`rcases` splits;
  - witnesses;
  - induction on a range sum;
  - step sequences;
  - fresh names.

  Verify with a doctest per builder and the parse fixture on each builder's output. The output must contain no `✝`.
- [x] 1.4 Move the exact LP into `toolkit/_lp.py` (public `solve_exact_lp`), keeping its tests. Technique-specific search stays out of the toolkit. Verify with the LP tests under `tests/toolkit/`, doctests, and the suite green.

## 2. Exact SOS solver (search-primitives)

- [x] 2.1 Implement `toolkit/_sos.py`: SOS from a numeric SDP (cvxopt), rounding, exact projection and an LDLᵀ check (D7). Verify on an irreducible quartic that is a sum of squares, on the old `sage_sos` inputs, and with a test showing that a problem whose rounding cannot be made exact reports failure instead of an inexact result.

## 3. Script tactic (script-tactic, project-scripts)

- [x] 3.1 Add the daemon method `run` (`problem`, `script`, `timeout_s`), which returns `{lean, stdout}`, binds the problem and toolkit, and resets symbolic state after each request. Verify with pytest: a script that assigns `proof`, a missing `proof`, a script that raises (stdout included), and a no-leak test for `assume`.
- [x] 3.2 Add the lenient extraction mode to `Veriphy/Kit/Problem.lean` (D2): every goal kind, and every nameable hypothesis with its text and an optional polynomial. Verify with Sage-free `#guard_msgs` tests in `VeriphyTest/Kit.lean` for a goal with `Real.sin` and a hypothesis that does not translate.
- [x] 3.3 Add the axiom guard to `closeAndEmit` (D3). Verify with Sage-free kit tests: a block using `sorry` is rejected with `sorryAx` named, `native_decide` is rejected with the axiom it introduces named, a `decide` proof is accepted, and the existing kit tests stay green.
- [x] 3.4 Add `Veriphy/Tactic/SageRun.lean` (`sage_run "<script>"` and `sage_run file "<path>"`): resolve and read the file against the workspace root, parse the returned text, run it through `closeAndEmit`, and produce the three-section combined error. Verify in `VeriphyTest.lean` with replay on:
  - a hint example, a `calc` derivation, a case split, a witness with a `norm_num` side goal, a matrix identity, a residual-goal rewrite, and a file-based script;
  - failing examples under `#guard_msgs`: an unparseable block, a wrong hint, a script that raises, `sorry`, and a missing file.
- [x] 3.5 Add `veriphy.certificates` (the header parser, and `list`/`show` through `python -m`). Verify with pytest on a directory holding complete and incomplete headers, and with a run of `sage -python -m veriphy.certificates list` on a scratch project.

## 4. Persistent session (daemon-session)

- [x] 4.1 Replace spawn-per-request in `Veriphy/Bridge.lean` with a session: one process per Lean process, a mutex, matched request ids, a timeout that kills the process, and a single retry on EOF (D9). Verify with a file running ten `sage_run` calls whose timing shows one start-up, and with `lake build VeriphyTest` green.
- [x] 4.2 Verify recovery and limits with scratch files:
  - killing the daemon between two calls (the second call succeeds);
  - a looping script (it fails after the limit, and the next call succeeds);
  - replay with a warm session (refused with the replay error).

## 5. Procedures, templates and benchmark (procedures)

- [x] 5.1 Create `VeriphyTest/Benchmark.lean` with every problem solved by a `sage_*` call in the pre-change `VeriphyTest.lean` (32 calls, including the regressions), each closed by `sage_run` following its recipe, with replay on. Verify that `lake build VeriphyTest.Benchmark` passes.
- [x] 5.2 Write `prompts/recipes/<technique>.md` for ideal membership, Farkas, SOS, factorization rewrite, witnesses, hint search, `calc` derivations, case splits, matrix identities and sums by induction. Each recipe gives when to use it, a template, a worked example (the benchmark's or one of 3.4's) and its failure modes. The technique-specific search (Farkas rows, `lift` cofactors, factorization, closed sums, product search with caps, witness search, root isolation) is Sage code inside the templates. Verify with a pytest check that every recipe's template matches the code of its tested example.
- [x] 5.3 Write `skills/certify/SKILL.md` (the build loop with catalog-first reuse and saving), add the recipe index and the save/reuse rules to `prompts/prove.md`, and point `skills/prove/SKILL.md` step 3 at `certify`. Rename the report category to `blocked-missing-building-block`. Verify by reading each against the procedures and project-scripts specs, and that `grep -rn blocked-missing-tactic` is empty outside `openspec/changes/archive`.

## 6. Remove ready-made certificates (checker-families, agent-certify, proof-reconstruction, oracle-methods)

- [ ] 6.1 Delete `sage_factor`, `sage_sos`, `sage_lincomb`, `sage_witness`, `sage_sum`, `sage_farkas`, `sage_exists`, `sage_certify` and `#sage_factor`/`#sage_sum`. Delete the daemon methods `factor`, `sos`, `roots`, `lincomb`, `farkas`, `exists`, `sum` and `certify`, the Lean reconstruction and the checkers only they used, and their tests (now covered by the benchmark). Verify that `lake build`, `lake build VeriphyTest`, `lake build VeriphyTest.Benchmark` and `nox -s tests` are green, that an unknown-method test exists for `farkas`, and that a grep finds no remaining references.
- [ ] 6.2 Document migration: a table in `docs/development/index.md` mapping each removed tactic to its recipe, a "Building proofs with sage_run" section in `docs/overview/user_guide.md`, README updates, and future work (a shared certificate repository). Verify that `nox -s docs -- build` succeeds without warnings.

## 7. Effectiveness gate and integration

- [ ] 7.1 Run the agent benchmark (D11): a fresh subagent with only the skills and procedures, given each benchmark statement with the proof blanked and no removed tactic names, works in a scratch Lake project that requires Veriphy and saves its scripts in that project's `certificates/`. Record the outcome, iterations and time per problem in `docs/development/benchmark.md`. Verify that every problem is solved. If any is not, improve a recipe, template or primitive and rerun. A tactic is never reinstated.
- [ ] 7.2 Run `uv run nox -s checks`, `uv run nox -s tests`, `lake build`, `lake build VeriphyTest`, `lake build VeriphyTest.Kit` and `lake build VeriphyTest.Benchmark`, all green. Then build the replayed replacements of every `sage_run` example with Sage off `PATH`, which must succeed. Push the branch and verify that CI is green.
- [ ] 7.3 Run `openspec validate sage-building-blocks --strict` and verify that it passes.

## Workflow follow-up

- Release through the template's flow (tag `X.Y.Z`), then archive the change with `/opsx:archive`.
- Future: a separate repository for shared, curated certificate scripts.
