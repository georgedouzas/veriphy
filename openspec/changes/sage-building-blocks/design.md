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
- The bespoke tactics stop being special. They become readable presets.

**Non-Goals:**
- Trusting Sage in any form. Numeric SOS is only a search: results are rationalized and verified exactly, and Lean re-checks them.
- A general CAS-to-Lean translator for transcendental functions. Non-polynomial hypotheses are visible to scripts as text only, and scripts handle them with Lean tactics they emit.
- Running Lean inside Sage. The loop is Lean calling Sage, never the reverse.
- Removing `sage_certify`. It stays, implemented as presets.

## Decisions

### D1. Script contract

A script runs in a fresh namespace with these pre-bound:
- `problem`, a `veriphy.toolkit.Problem`: ring, generators, atoms with Lean text, hypotheses as `Hyp(name, poly | None, rel | None, text)`, the goal (polynomial form when one exists, always its text), and binders;
- the toolkit's public names;
- `sage.all`.

The script assigns `proof`, either a toolkit `Lean` value or a string. The new daemon method `run` takes `{problem, script | preset, args, timeout_s}` and returns `{lean, stdout}`. Errors keep the existing `ScriptError` path, which carries stdout. `run` is not advisory: its result is Lean text, which Lean checks.

### D2. Lean side of `sage_run`

1. **Extraction** uses a new lenient mode: `ExtractOpts.lenient := true`.
   - Every relation goal is accepted, as are `False`, `∃` and any other proposition, with its polynomial form when it translates.
   - Every nameable hypothesis is included, with its text, and with a polynomial form when it translates.
2. **Parsing:** the returned text is parsed with `Parser.runParserCategory env `tactic text "<sage_run>"`. Parse errors carry line and column within the text.
3. **Running** goes through `closeAndEmit`. On any failure the error is re-raised with three sections (`script output`, `Lean text`, `Lean error`), so the agent gets the combined feedback in one message.
4. `sage_run` is a plain tactic with syntax `sage_run str`. A file variant (`sage_run from "path"`) is out of scope.

### D3. Axiom guard in `closeAndEmit`

After the tactic runs, the guard instantiates the original goal's assignment.
- It rejects the proof if `Expr.hasSorry` holds.
- Otherwise it collects every constant in the term and runs `collectAxioms` on each (the results are cached per constant). It rejects any axiom outside `{propext, Classical.choice, Quot.sound}`, which catches `Lean.ofReduceBool` from `native_decide` and any custom axiom.

The guard lives in `closeAndEmit`, so every tactic, presets included, is covered. Residual goals are allowed, because metavariables in the term are skipped. *Alternative:* guard only `sage_run`. Rejected, because one guard at the shared exit is simpler and stronger.

### D4. Toolkit layout and dependency direction

Following the constitution, imports run downward: `core` → `toolkit` → `oracle` / `presets` → `sage_server`.

```
src/veriphy/toolkit/__init__.py     public surface (__all__), doctests run under Sage
toolkit/_problem.py                 Problem, Hyp (moved from oracle/_scripts.py and widened)
toolkit/_lean.py                    Lean value (text + category), rendering of rationals and polynomials over atoms
toolkit/_emit.py                    builders: linear_combination, sq_nonneg/mul_*, hint calls, rw-show, calc, cases, witness, steps
toolkit/_algebra.py                 exact LP (moved), cofactors, factorization, normal forms, Farkas (moved)
toolkit/_positivity.py              nlinarith product search, SOS (factor, hinted, SDP + rationalize + verify)
toolkit/_structure.py               roots, rational points (moved from exists), root isolation, sign/case enumeration, matrices
src/veriphy/presets/                one module per preset: factor, sos, lincomb, witness, farkas, exists, certify_*
```

The oracle methods `factor`, `sos`, `lincomb`, `farkas` and `exists` become thin wrappers over the toolkit, so the protocol stays compatible. `run` executes scripts and presets. The toolkit is the public surface for script authors, and each public name has a doctest.

### D5. Emitters produce typed text

`Lean` is a frozen dataclass `(text, kind)`, where `kind` is `term` or `tactic`, and builders check the kinds they combine. Polynomials render over the atoms' text, with every non-identifier atom parenthesized and rationals written as `n / d`. Fresh names are chosen against the problem's hypothesis names, which gives the Python counterpart of `freshIdent`.

Emitters do not try to typecheck. Lean does that, and its error comes back in the combined feedback (D2). The emitter guarantee is syntactic: the output parses in its category. Tests check this by parsing emitted text through `lake env lean`, using a small pytest fixture that writes a scratch file.

### D6. nlinarith product search

Candidate products are formed from:
- pairwise products of the nonnegative hypothesis forms (`b - a ≥ 0` for `a ≤ b`);
- squares of the hypothesis polynomials;
- squares of pairwise differences of atoms and of degree ≤ 1 combinations suggested by the goal's monomials.

The search is an exact LP, as in Positivstellensatz degree 2. It looks for nonnegative weights on the candidates and hypotheses, plus a free multiple of each equality, that make `goal_slack` equal a nonnegative constant. It returns the products with nonzero weight as `nlinarith` hints. Candidate count and degree are capped (defaults 60 and 4) to keep it fast. *Alternative:* emit the full `linear_combination` certificate. That is also offered (`as_linear_combination=True`), but hints are the default because `nlinarith` is more robust to small mismatches.

### D7. SOS via SDP, then exact

1. Solve the Gram-matrix SDP numerically (cvxopt).
2. Round the entries to rationals with bounded denominators.
3. Project onto the affine space of exact coefficient matching (an exact linear solve).
4. Check positive semidefiniteness exactly with an LDLᵀ decomposition over QQ.

If any step fails, report "no exact SOS found". The result is a list of `(c, q)` squares, which the existing squares emitter consumes.

### D8. Presets replace bespoke Lean

Each of `sage_factor`, `sage_sos`, `sage_lincomb`, `sage_witness`, `sage_farkas` and `sage_exists` becomes a single line, `elab "sage_x" … => runPreset "x" args`, which reaches `run` with `preset := "x"`. `sage_sos [hints]` passes its hints as extra translated terms in `args`. `sage_factor` keeps its residual goal, because its preset emits the `refine Eq.trans (show … by ring1) ?_` step. `sage_sum` needs no Sage and stays a Lean-only family. `sage_certify` becomes three presets that run the user's script and convert its certificate with the emitters.

The printed replacements may change in surface form, and the existing tests pin their behavior. `Veriphy/Kit/Build.lean`'s certificate builders stay for `sage_sum` and the kit tests, and any that become unused are removed.

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
3. **build with `sage_run`**: inspect `problem`, pick primitives, emit Lean, iterate on the combined feedback; presets are listed as shortcuts;
4. the advisory oracle;
5. recursion.

The report category becomes `blocked-missing-building-block`. The user guide gets a "Building proofs with sage_run" section with worked examples (hint, calc, case split, matrix and witness), and every example is also a test in `VeriphyTest.lean`.

## Risks / Trade-offs

- **[Risk]** Free-form Lean text makes failures less structured than fixed families. → The combined feedback (D2) and well-formed emitters (D5) cover most of it, and the agent iterates quickly thanks to the session (D9).
- **[Risk]** Parallel elaboration with one daemon could serialize work or deadlock. → A single mutex and request-id matching serialize requests. Throughput is bounded by Sage, which is single-threaded anyway, and the time limit prevents a stuck lock holder.
- **[Risk]** `collectAxioms` on large proof terms is slow. → It runs per constant with a cache, and only once per successful tactic.
- **[Risk]** The product search can blow up combinatorially. → Candidate and degree caps, configurable per call. On failure the search reports "no product certificate", and the agent can supply its own candidates.
- **[Risk]** SDP rounding fails on degenerate problems. → The search is exact-verified or reports failure, never wrong, and hinted SOS remains available.
- **[Trade-off]** Presets in Python mean the Lean side no longer shows certificate logic. In exchange, the agent can read and adapt the presets, which is the point of the change.
- **[Trade-off]** Renaming the report category breaks callers who parse `blocked-missing-tactic`. Callers are agents reading markdown, and the playbook defines the vocabulary.

## Migration Plan

1. Merge `package-and-distribute`.
2. Add the toolkit next to the oracle, moving functions over with their tests.
3. Add `sage_run` and the axiom guard.
4. Add the session.
5. Migrate tactics to presets one at a time, keeping `VeriphyTest.lean` green after each.
6. Rewrite the docs.

Rollback per step is a revert, and committed downstream proofs are unaffected because they contain only replacements.

## Open Questions

- The default candidate cap and degree for the product search (60 and 4 are starting points). Tune against the test examples during implementation. This does not change the interfaces.
