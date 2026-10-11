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
   c. decompose: isolate the computational core (polynomial identity,
      inequality, closed-form sum, rational root, linear system, witness) and
      send it to the matching `sage_*` certificate tactic; prove the glue
      yourself. Matching: identity from hypotheses → `sage_lincomb` (also
      kernel spans); factorization → `sage_factor`; `0 ≤ p` → `sage_sos`
      (pass candidate squares `sage_sos [q₁, …]` when `p` is a known sum of
      squares that does not factor); large linear (in)feasibility, where
      `linarith` times out → `sage_farkas`; `∃` with a rational witness
      (eigenvector, feasible point, counterexample) → `sage_exists`;
      closed-form sum → `#sage_sum` then `sage_sum n`
   d. one-off certificate: when no `sage_*` tactic fits but the proof has a
      checkable shape, write the certificate yourself in Sage with
      `sage_certify <family> "<script>"`. The script sees the goal and
      context already normalized — `R`, generators `x0, x1, …` (one per atom;
      `atoms` maps each to its Lean text), `hyps` as `Hyp(name, poly, rel)`
      meaning `poly rel 0` with `rel ∈ eq/le/lt/ne`, `goal` (same shape),
      `binders`/`body` for `∃` — and must assign `certificate`:
      - `identity` (goal `a = b`): `{'cofactors': {hyp_name: poly}}`, checked
        by `linear_combination`;
      - `inequality` (goal `a ≤ b`, `a < b` or `False`):
        `{'weights': {hyp_name: w}, 'squares': [(c, q), …]}` — `w ≥ 0`
        rationals on `≤`/`<` hypotheses (polynomials allowed on `=`), `c ≥ 0`
        — checked by `linear_combination` with `sq_nonneg q` terms (for
        `False`, through the constant the combination reduces to);
      - `witness` (goal `∃ x₁ … xₙ, …`): `[v₁, …, vₙ]` rationals, checked by
        `norm_num`.
      A wrong certificate just fails; the script's printed output comes back
      in the error, so iterate. Commit the emitted `Try this:` (plain
      `linear_combination` / `exact ⟨…⟩`), never the `sage_certify` call.
   e. oracle: when stuck on *what the proof even is* — solving an equation
      system (a kernel computation, an equilibrium, a change of variables),
      finding the case split, locating the closed form — ask the bridge's
      advisory methods (`solve`, `symbolic_check`, `matrix_check`). When the
      exploration is session-shaped rather than query-shaped — deriving
      representation matrices, testing a decomposition scheme on random
      samples, generating Lean-ready tables — send a whole derivation script
      through `run_script` and read back its structured `results`. All of it
      is UNTRUSTED guidance: never transcribe it into the proof; re-prove in
      Lean whatever you take from it.
   f. recursion: if a sub-lemma is missing, prove it first (lemmas only —
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
     would have closed it, and no checker family can verify that certificate
     (so `sage_certify` could not express it either — describe the
     certificate and the checker it would need);
   - `statement-suspect`: the numeric test contradicted the claim (give the
     counterexample).

   What to do with the result — commit, PR, record-keeping — is the caller's
   decision, not this playbook's.
