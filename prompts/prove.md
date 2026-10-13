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
  `echo '{"id":1,"method":"ping"}' | sage -python -m veriphy.sage_server`
  (if it is missing: `sage -pip install veriphy`).

## Loop

1. **Formalize the statement** (skip if the caller gave formal Lean). Mimic
   the target file's local conventions. Then run BOTH lie detectors:
   - *Round-trip*: informalize your formal statement back to English; compare
     with the original. Any semantic drift → redo.
   - *Identity test*: when the claim is (or reduces to) an identity, try the
     bridge's `symbolic_check` first (`matrix_check` when matrices are
     involved — representation identities, Clifford relations, determinant
     formulas) — symbolic equality under the stated assumptions is strictly
     stronger than sampling and catches branch-cut and measure-zero traps. If
     it returns `equal: null` (undecided) or the claim doesn't fit, fall back
     to rendering the statement in Sage and evaluating at ≥10 random parameter
     values satisfying the hypotheses. A counterexample means your
     formalization (or the original claim) is wrong — stop and report which.

2. **Compile-fix.** Iterate on compiler errors until the statement type-checks
   with `sorry` as the proof. Use LSP/REPL/`lake build` feedback, never guess
   blind.

3. **Prove.** In order of cheapness:
   a. `simp` / `norm_num` / `positivity` / `nlinarith` / `fun_prop` / `gcongr`
   b. premise search (loogle, LeanSearch, `exact?`) for the missing lemma
   c. build a certificate: isolate the computational core (polynomial
      identity, inequality, closed-form sum, root, linear system, witness,
      matrix identity) and build its proof with `sage_run`, following
      `prompts/certify.md`. Prove the glue yourself. Veriphy ships no
      ready-made certificates. You create each one from the recipes, reusing
      what the project already has:
      - first `sage -python -m veriphy.certificates list` in the project, and
        adapt a saved script whose `goal` matches;
      - otherwise pick a recipe from the index below, copy its template into
        the project's `.veriphy/certificates/`, adapt it, and run it.

      | goal shape | recipe |
      |---|---|
      | `a = b` from equality hypotheses | `ideal_membership` |
      | `False`, `a ≤ b`, `a < b` linear in the hypotheses | `farkas` |
      | `0 ≤ p`, `p` polynomial | `sos` |
      | polynomial inequality needing products or squares | `hint_search` |
      | `lhs = rhs` where the factored `lhs` helps | `factor_rewrite` |
      | `∃ x₁ … xₙ, …` with rational values | `witness` |
      | `∑ k ∈ Finset.range n, f k = F n` | `sum_induction` |
      | long manipulation through intermediate forms | `calc_derivation` |
      | easy on each side of a condition | `case_split` |
      | identity between explicit matrices | `matrix_identity` |
      | `lhs ≤ rhs` with divisions (rational functions) | `rational_inequality` |
      | identity of `exp`, `log`, `sqrt`, `sin`, `cos` by named lemmas | `transcendental_rewrite` |
      | `!![…]` identity, `det` or `trace` written in the goal | `matrix_from_goal` |
      | `deriv (fun x => f x) a = v` with an explicit `f` | `derivative` |
      | ODE in `deriv x`, `x` given by `hx : x = fun s => …` or asked for by `∃ x` | `ode_solution` |

      Recipes are in `prompts/recipes/<name>.md`. Read only the one you use.

      Recipes for one library live in `prompts/recipes/<library>/` and apply
      only when that library's pack is active (`#veriphy_tables` lists the
      active namespaces). They use the library's own definitions and sign
      conventions, recorded in its pack.
      Save a script that closed its goal into the project's `.veriphy/certificates/`,
      with its header, so the next similar goal reuses it.
   d. oracle: when stuck on *what the proof even is* — solving an equation
      system (a kernel computation, an equilibrium, a change of variables),
      finding the case split, locating the closed form — ask the bridge's
      advisory methods (`solve`, `symbolic_check`, `matrix_check`). When the
      exploration is session-shaped rather than query-shaped — deriving
      representation matrices, testing a decomposition scheme on random
      samples, generating Lean-ready tables — send a whole derivation script
      through `run_script` and read back its structured `results`. All of it
      is UNTRUSTED guidance: never transcribe it into the proof; re-prove in
      Lean whatever you take from it.
   e. recursion: if a sub-lemma is missing, prove it first (lemmas only —
      never invent definitions; flag those to the caller).
   Budget: stop after ~30 min wall clock or 3 decomposition attempts.

4. **Verify.** `lake build` from clean. Zero `sorry`. The final proof must not
   invoke Sage — commit only the `Try this:` replacements `sage_run` emits.

5. **Report to the caller** — one of:
   - `proved`: the verified Lean proof (file/diff), noting which recipes and
     saved scripts were used, if any;
   - `blocked-library-gap`: the statement needs theory that doesn't exist yet
     (name precisely what);
   - `blocked-missing-building-block`: the proof needs a Sage computation or
     a Lean emitter that the toolkit lacks, so no `sage_run` script can build
     it. Name the missing primitive or emitter, and the certificate it would
     produce;
   - `statement-suspect`: the numeric test contradicted the claim (give the
     counterexample).

   What to do with the result — commit, PR, record-keeping — is the caller's
   decision, not this playbook's.
