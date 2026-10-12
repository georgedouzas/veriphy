# Design

## Context

The motivation is in proposal.md (Why). The state this change builds on, after `package-and-distribute`:

- **Lean.**
  - `Veriphy/Kit/` provides `withProblem` (extraction to a polynomial `Problem`, which fails on non-polynomial goals), the builders, the checker families and `closeAndEmit` (run what you print, then replay, then one suggestion).
  - Seven tactics plus `sage_certify` sit on that kit: about 350 lines in `Veriphy/Tactic/`.
  - The bridge spawns `sage -python -m veriphy.sage_server` once per request, at about 2 s each.
- **Python (`src/veriphy`, under the constitution).**
  - `oracle` holds the methods (`factor`, `sos`, `lincomb`, `farkas`, `exists`, `run_script`, `certify`, …), registered in per-module tables.
  - `_scripts` already binds a serialized problem into a script namespace (`_Problem`, `Hyp`) and runs preparsed Sage under a timeout.
- **Available on SageMath 10.9:** `SemidefiniteProgram` with the cvxopt backend (cvxopt 1.3.3), so numeric SOS is possible.
- **Available on Lean v4.34.1:** `Lean.collectAxioms` and `Std.Sync.Mutex`.

## Goals / Non-Goals

**Goals:**
- Any proof a Sage script can assemble out of Lean text is reachable through one tactic, and only standard axioms are ever accepted.
- The toolkit makes the common shapes one-liners: hints, `calc` chains, case splits, witnesses, `linear_combination`.
- A script-then-check iteration costs well under a second after the first call.
- Veriphy ships no ready-made certificates. Its value is the procedures, templates and skills that make creating one cheap, and they are proven at least as effective as the tactics they replace.

**Non-Goals:**
- Trusting Sage in any form. Numeric SOS is only a search: results are rationalized and verified exactly, and Lean re-checks them.
- A general CAS-to-Lean translator for transcendental functions. Non-polynomial hypotheses are visible to scripts as text only, and scripts handle them with Lean tactics they emit.
- Running Lean inside Sage. The loop is Lean calling Sage, never the reverse.
- A shared certificate repository across projects (future work, a separate repo).

## Decisions

### D1. Script contract

A script runs in a fresh namespace with these pre-bound:
- `problem`, a `veriphy.toolkit.Problem`: ring, generators, atoms with Lean text, hypotheses as `Hyp(name, poly | None, rel | None, text)`, the goal (polynomial form when one exists, always its text), and binders;
- the toolkit's public names;
- `sage.all`.

The script assigns `proof`, either a toolkit `Lean` value or a string. The new daemon method `run` takes `{problem, script, timeout_s}` and returns `{lean, stdout}`. Errors keep the existing `ScriptError` path, which carries stdout. `run` is not advisory: its result is Lean text, which Lean checks.

### D2. Lean side of `sage_run`

1. **Extraction** uses a new lenient mode: `ExtractOpts.lenient := true`.
   - Every relation goal is accepted, as are `False`, `∃` and any other proposition, with its polynomial form when it translates.
   - Every nameable hypothesis is included, with its text, and with a polynomial form when it translates.
2. **Parsing:** the returned text is parsed with `Parser.runParserCategory env `tactic text "<sage_run>"`. Parse errors carry line and column within the text.
3. **Running** goes through `closeAndEmit`. On any failure the error is re-raised with three sections (`script output`, `Lean text`, `Lean error`), so the agent gets the combined feedback in one message.
4. `sage_run` takes either an inline script (`sage_run "<script>"`) or a project file (`sage_run file "certificates/<name>.sage"`, see D12).

### D3. Axiom guard in `closeAndEmit`

After the tactic runs, the guard instantiates the original goal's assignment.
- It rejects the proof if `Expr.hasSorry` holds.
- Otherwise it collects every constant in the term and runs `collectAxioms` on each (the results are cached per constant). It rejects any axiom outside `{propext, Classical.choice, Quot.sound}`, which catches `Lean.ofReduceBool` from `native_decide` and any custom axiom.

The guard lives in `closeAndEmit`, so every tactic that emits a replacement is covered. Residual goals are allowed, because metavariables in the term are skipped. *Alternative:* guard only `sage_run`. Rejected, because one guard at the shared exit is simpler and stronger.

### D4. Toolkit layout and dependency direction

Following the constitution, imports run downward: `core` → `toolkit` → `oracle` → `sage_server`.

```
src/veriphy/toolkit/__init__.py     public surface (__all__), doctests run under Sage
toolkit/_problem.py                 Problem, Hyp (moved from oracle/_scripts.py and widened)
toolkit/_lean.py                    Lean value (text + category), rendering of rationals and polynomials over atoms
toolkit/_emit.py                    builders: linear_combination, sq_nonneg/mul_*, hint calls, rw-show, calc, cases, witness, refute, steps
toolkit/_lp.py                      exact LP (moved)
toolkit/_sos.py                     SOS from a numeric SDP, rounded, projected and verified exactly
```

**What the toolkit holds:** only what is general and hard to get right in a few lines at proof time. That means problem binding, emitters, the exact LP and exact SOS from an SDP. Technique-specific search (Farkas rows, `lift` cofactors, factorization, closed sums, product search, witnesses, root isolation, matrix decompositions) is a few lines of Sage over these. It lives in the recipes' templates, where the agent sees it and adapts it, and the benchmark tests it.

The oracle methods `factor`, `sos`, `roots`, `lincomb`, `farkas`, `exists`, `sum` and `certify` are removed once their tactics are, and their algorithms live on as toolkit primitives. `run` executes scripts. The toolkit is the public surface for script authors, and each public name has a doctest.

### D5. Emitters produce typed text

`Lean` is a frozen dataclass `(text, kind)`, where `kind` is `term` or `tactic`, and builders check the kinds they combine. Polynomials render over the atoms' text, with every non-identifier atom parenthesized and rationals written as `n / d`. Fresh names are chosen against the problem's hypothesis names, which gives the Python counterpart of `freshIdent`.

Emitters do not try to typecheck. Lean does that, and its error comes back in the combined feedback (D2). The emitter guarantee is syntactic: the output parses in its category. Tests check this by parsing emitted text through `lake env lean`, using a small pytest fixture that writes a scratch file.

### D6. Hint search is a recipe

The `nlinarith` product search is a technique: form candidate products and squares from the hypotheses and the goal, then find nonnegative weights with `solve_exact_lp` that leave a nonnegative constant slack. It is written as the hint-search recipe's template (capped candidates, for example 60), not as a toolkit function.

### D7. SOS via SDP, then exact (`toolkit/_sos.py`)

1. Solve the Gram-matrix SDP numerically (cvxopt).
2. Round the entries to rationals with bounded denominators.
3. Project onto the affine space of exact coefficient matching (an exact linear solve).
4. Check positive semidefiniteness exactly with an LDLᵀ decomposition over QQ.

If any step fails, report "no exact SOS found". The result is a list of `(c, q)` squares, which the `sq_nonneg` and `linear_combination` emitters consume. Factor-based and hinted SOS are recipe code (`p.factor()`, and `solve_exact_lp` over hinted squares).

### D8. Procedures replace ready-made certificates

The certificate tactics and `sage_certify` are deleted, with the daemon methods and Lean reconstruction only they used (`Kit/Build.lean`'s certificate builders and the `Kit/Family.lean` checkers; `closeAndEmit`, extraction and replay stay).

Their knowledge becomes procedures in agent-agnostic markdown, `prompts/recipes/<technique>.md`, one per technique. Each recipe has:
- **When to use:** the goal shapes it fits and the signals that it applies;
- **Template:** a fill-in `sage_run` script using toolkit primitives and emitters;
- **Worked example:** the template instantiated, which is also a test;
- **Failure modes:** symptoms in the combined feedback and the next step for each (for example "κ not constant: a nonlinear hypothesis was weighted; drop it or switch to hint search").

`prompts/prove.md` gets a recipe index (a decision table from goal shape to recipe), and the agent loads one recipe at a time. A new `skills/certify/SKILL.md` is a short skill for the build loop that points into the recipes. `skills/prove` delegates to it in step 3. A mapping table in `docs/development/index.md` takes each removed tactic to its recipe, for users migrating a call.

### D11. Benchmark and the effectiveness gate

`VeriphyTest/Benchmark.lean` holds every problem a removed tactic solved: the 32 calls of the pre-change `VeriphyTest.lean`, which include the anomaly no-go system, SOS potentials and eigenvector witnesses from the physics work. Each problem is closed with `sage_run` following its recipe, with replay on. This is the mechanical half of the gate.

The agent half: a fresh subagent gets the skills and procedures, and the benchmark statements with proofs blanked and the old tactic names stripped from its context. It must close every problem. A script records the outcome, iterations and wall time per problem into `docs/development/benchmark.md`. Any unsolved problem blocks the change, and the fix is a better recipe, template or primitive, never a reinstated tactic.

### D9. Session

The bridge keeps one daemon session per Lean process:
- `initialize session : IO.Ref (Option Session)`, guarded by a `Std.Mutex`, since Lean elaborates declarations in parallel;
- a `Session` holds the child process and its stdin and stdout handles, and request ids increase so responses are matched to requests.

Requests behave as follows:
- **Timeout:** each request reads its response in a task raced against a timer (default 150 s, above the script limit of 120 s). On timeout, the child is killed and the session cleared.
- **Recovery:** an EOF or broken pipe clears the session, and the request is retried once with a new process.
- **Replay:** the existing option guard runs before the session is touched.

On the Python side, each request already uses a fresh namespace. `run` also calls `forget()` and resets symbolic variables after every request. The spawn-per-request code path is removed.

### D10. Agent workflow

`prompts/prove.md` step 3 is reorganized:
1. cheap mathlib automation;
2. premise search;
3. **build with `sage_run`**: look for an existing project script, otherwise pick a recipe, adapt its template, emit Lean, iterate on the combined feedback, and save the script that worked;
4. the advisory oracle;
5. recursion.

The report category becomes `blocked-missing-building-block`. The user guide gets a "Building proofs with sage_run" section with worked examples (hint, calc, case split, matrix and witness), and every example is also a test in `VeriphyTest.lean`.

### D12. Certificate scripts live in the caller's project

Scripts an agent or user creates belong to the project being proved, never to Veriphy:
- **Location:** one `.sage` file per certificate in `certificates/` at the Lake workspace root. `sage_run file "certificates/<name>.sage"` resolves the path against the workspace root, which is Lean's working directory under Lake.
- **Header:** each script starts with a comment block giving `name`, `technique` (the recipe it follows), `goal` (the goal shape it closes) and a one-line `description`.
- **Catalog:** `sage -python -m veriphy.certificates list [dir]` (a small static module in the package) prints the catalog from those headers, so any agent can discover what a project already has. `… show <name>` prints one script.
- **Workflow:** the playbook makes the agent check the catalog before writing a script, prefer adapting a matching one, and save a successful script with its header. Saved scripts are reusable on any goal of the same shape, because they read the bound `problem`.
- **What gets committed:** the proof in Lean files is always the emitted replacement, so it builds without Sage. Committing `certificates/` is the caller's choice, and the scripts are its reusable source.

A shared repository of certificates, curated across projects, is future work for a separate repo. It is out of scope here.

## Risks / Trade-offs

- **[Risk]** Free-form Lean text makes failures less structured than fixed families. → The combined feedback (D2) and well-formed emitters (D5) cover most of it, and the agent iterates quickly thanks to the session (D9).
- **[Risk]** Parallel elaboration with one daemon could serialize work or deadlock. → A single mutex and request-id matching serialize requests. Throughput is bounded by Sage, which is single-threaded anyway, and the time limit prevents a stuck lock holder.
- **[Risk]** `collectAxioms` on large proof terms is slow. → It runs per constant with a cache, and only once per successful tactic.
- **[Risk]** The hint-search recipe can blow up combinatorially. → Its template caps candidates and degree. The agent can adjust the caps or supply its own candidates.
- **[Risk]** SDP rounding fails on degenerate problems. → The search is exact-verified or reports failure, never wrong, and hinted SOS remains available.
- **[Trade-off]** Users lose one-word tactics, and each certificate costs a short script. This is accepted, because the long tail needs creation anyway. Recipes keep common cases to a few lines, and the benchmark proves no previously solved problem regresses.
- **[Risk]** An agent following recipes does worse than the hard-coded tactics did. → The agent benchmark (D11) is a release gate, and failures improve recipes or primitives.
- **[Trade-off]** Renaming the report category breaks callers who parse `blocked-missing-tactic`. Callers are agents reading markdown, and the playbook defines the vocabulary.

## Migration Plan

1. Merge `package-and-distribute`.
2. Add the toolkit next to the oracle, moving functions over with their tests.
3. Add `sage_run` and the axiom guard.
4. Add the session.
5. Write the recipes and port each benchmark problem to `sage_run`. Then remove the tactics, methods and reconstruction.
6. Write the skills and docs, then run the agent benchmark as the gate.

Rollback per step is a revert, and committed downstream proofs are unaffected because they contain only replacements.

## Open Questions

- The default candidate cap and degree in the hint-search template (60 and 4 are starting points). Tune against the benchmark.
