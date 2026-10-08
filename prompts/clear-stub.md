# Playbook: clear one PhysLean informal stub

Agent-agnostic instructions (the spec-kit pattern: logic lives here; per-agent
adapters in `.claude/skills/`, `.cursor/commands/`, etc. just point at this file).

## Preconditions

- This repo builds: `lake build` succeeds.
- PhysLean is checked out as a sibling or dependency; `lake build` green there too.
- Sage daemon answers: `echo '{"id":1,"method":"ping"}' | sage -python sage_bridge/server.py`

## Loop

1. **Pick.** Grep PhysLean for `informal_lemma` / `informal_definition`. Choose a
   stub whose `deps` are all formalized. Prefer lemmas over definitions
   (definitions need human design review — flag them, don't invent them).

2. **Formalize the statement.** Write the Lean statement next to the stub,
   mimicking the file's local conventions. Then run BOTH lie detectors:
   - *Round-trip*: informalize your formal statement back to English; compare
     with the stub's docstring. Any semantic drift → redo.
   - *Numeric test*: render the statement in Sage, evaluate at ≥10 random
     parameter values satisfying the hypotheses. A counterexample means your
     formalization (or the stub) is wrong — stop and record which.

3. **Compile-fix.** Iterate on compiler errors until the statement type-checks
   with `sorry` as the proof. Use the LSP/REPL feedback, never guess blind.

4. **Prove.** In order of cheapness:
   a. `simp` / `norm_num` / `positivity` / `fun_prop` / `gcongr`
   b. premise search (loogle, LeanSearch, `exact?`) for the missing lemma
   c. decompose: isolate the computational core (polynomial identity,
      inequality, closed-form sum, branching rule) and send it to the matching
      `sage_*` certificate tactic; prove the glue yourself
   d. recursion: if a sub-lemma is missing from mathlib/PhysLean, add it to the
      queue as a new stub and prove it first (lemmas only — never definitions).
   Budget: stop after ~30 min wall clock or 3 decomposition attempts.

5. **Verify.** `lake build` from clean. Zero `sorry`, zero warnings you added.
   Committed proofs must not invoke Sage (only `Try this:` outputs are allowed
   in the final diff).

6. **Log.** Append one row to `bench/ledger.md`: stub name, outcome
   (cleared / blocked-mathlib-gap / blocked-missing-tactic / statement-suspect),
   what was missing, wall-clock time, approximate cost.

7. **PR.** Branch, commit, open a PR against PhysLean. The PR description states
   the informal stub, the formal statement, and the round-trip/numeric evidence
   from step 2. Human review is for the *statement's faithfulness*; the kernel
   already reviewed the proof.

## Outcome taxonomy (step 6) — failures are data, not noise

- `blocked-mathlib-gap`: the statement can't be expressed or a whole theory is
  missing (e.g. elliptic integrals, π₁ of Lie groups). These rows are the
  "gap map" — the project's most valuable output.
- `blocked-missing-tactic`: a Sage capability with a checkable certificate
  would have closed it. These rows prioritize the Veriphy tactic roadmap.
- `statement-suspect`: numeric testing contradicted the stub. Report upstream.
