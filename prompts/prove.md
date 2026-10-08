# Playbook: produce a verified proof of one physics statement

Agent-agnostic instructions (the spec-kit pattern: logic lives here; per-agent
adapters in `.claude/skills/`, `.cursor/commands/`, etc. just point at this file).

Veriphy is a tool, not a campaign: the **caller supplies the target** — a Lean
statement to prove, an informal statement to formalize and prove, or a repo +
backlog item (e.g. a Physlib `informal_lemma`). The caller also owns the
outcome: this playbook ends by *reporting*, never by opening PRs, keeping
score, or committing to the target repo beyond what the caller asked for.

## Preconditions

- Veriphy builds: `lake build` in this repo succeeds.
- If the statement refers to another library's definitions, the caller has
  provided that library (checked out and building), and a workspace exists
  whose lakefile requires both it and Veriphy. Create one if needed; it is
  disposable.
- Sage daemon answers:
  `echo '{"id":1,"method":"ping"}' | sage -python sage_bridge/server.py`
  (set `VERIPHY_SAGE_SERVER` to the script's absolute path when building
  outside this repo).

## Loop

1. **Formalize the statement** (skip if the caller gave formal Lean). Mimic
   the target file's local conventions. Then run BOTH lie detectors:
   - *Round-trip*: informalize your formal statement back to English; compare
     with the original. Any semantic drift → redo.
   - *Numeric test*: render the statement in Sage, evaluate at ≥10 random
     parameter values satisfying the hypotheses. A counterexample means your
     formalization (or the original claim) is wrong — stop and report which.

2. **Compile-fix.** Iterate on compiler errors until the statement type-checks
   with `sorry` as the proof. Use LSP/REPL/`lake build` feedback, never guess
   blind.

3. **Prove.** In order of cheapness:
   a. `simp` / `norm_num` / `positivity` / `nlinarith` / `fun_prop` / `gcongr`
   b. premise search (loogle, LeanSearch, `exact?`) for the missing lemma
   c. decompose: isolate the computational core (polynomial identity,
      inequality, closed-form sum, rational root) and send it to the matching
      `sage_*` certificate tactic; prove the glue yourself
   d. recursion: if a sub-lemma is missing, prove it first (lemmas only —
      never invent definitions; flag those to the caller).
   Budget: stop after ~30 min wall clock or 3 decomposition attempts.

4. **Verify.** `lake build` from clean. Zero `sorry`. The final proof must not
   invoke Sage — commit only the `Try this:` replacements the tactics emit.

5. **Report to the caller** — one of:
   - `proved`: the verified Lean proof (file/diff), noting which `sage_*`
     tactics were used, if any;
   - `blocked-library-gap`: the statement needs theory that doesn't exist yet
     (name precisely what);
   - `blocked-missing-tactic`: a Sage capability with a checkable certificate
     would have closed it (describe the certificate);
   - `statement-suspect`: the numeric test contradicted the claim (give the
     counterexample).

   What to do with the result — commit, PR, record-keeping — is the caller's
   decision, not this playbook's.
