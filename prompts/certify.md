# Building a certificate with `sage_run`

Use this when a goal's computational core needs Sage: coefficients, squares,
multipliers, witnesses, closed forms, or intermediate expressions. Sage finds
them, and Lean checks the proof you emit. Sage is never trusted.

## The loop

1. **Inspect the problem.** A first script can just print what it sees:

   ```lean
   sage_run "print(goal_kind, goal); print(hyps); print(atoms); proof = 'sorry'"
   ```

   The run fails on purpose: the `sorry` is rejected. The error shows the
   script output.
   - `goal` and each hypothesis are `Hyp(name, poly, rel, text)`, meaning
     `poly rel 0` over generators `x0, x1, …`.
   - `atoms` maps each generator to its Lean text.
   - `lhs` and `rhs` are the goal's sides.
   - A hypothesis with no polynomial form has `poly = None`, and keeps its
     `text`.
2. **Reuse before writing.** Run `sage -python -m veriphy.certificates list` in
   the project. Each line starts with the script's path, which is what
   `sage_run file` takes. `show <name>` prints a script, so you can read its
   code when the header is not enough to judge a match. A saved script reads
   the bound `problem`, so it usually runs unchanged on a goal of the same
   shape.
3. **Otherwise pick a recipe.** Use the index in `prompts/prove.md` step 3, then
   read `prompts/recipes/<name>.md`. Copy its template to
   `certificates/<specific_name>.sage` in the project. Adapt the `EDIT` lines,
   and update the header: `name` the same as the file name, plus an accurate
   `goal` and `description`. A script with goal-specific edits, such as
   hard-coded `HINTS`, gets a goal-specific name, so it is not mistaken for a
   general one. Never delete or rename a script someone else saved.
4. **Run it:** `sage_run file "certificates/<specific_name>.sage"`.
5. **Iterate on the feedback.** A failure shows the script's output, the Lean
   text it built, and Lean's error. The recipe's "Failure modes" section maps
   each symptom to the next step. A script that raises shows its traceback and
   output.
6. **Commit the replacement.** Replace the `sage_run` call with the emitted
   `Try this:` block, parentheses included. The `[apply]` marker in the message
   is not part of the proof. That block is the proof, and it builds without
   Sage. Keep the script in `certificates/` with a complete header, for reuse.

Shape the goal first. Introduce hypotheses (`intro`) and split conjunctions
before calling `sage_run`, so the script sees a relation or `∃` it can work
with, not an implication. An implication arrives as `goal_kind == 'other'`.

## The toolkit, pre-bound in every script

- **Problem:** `problem`, `R`, `x0, x1, …`, `hyps`, `goal`, `goal_kind`,
  `binders`, `body`, `atoms`, `lhs`, `rhs`, `Hyp`.
- **Symbolic forms:** every hypothesis and the goal carry `.expr`, the Sage
  symbolic form of `lhs - rhs` (with `sqrt`, `exp`, `log`, `sin`, `cos`, `tan`,
  `abs`, `pi`, `I`, range sums, `!![…]` matrices, `det`, polynomial `eval`),
  over `symbols` (the same names as `x0, x1, …`, in Sage's symbolic ring).
  `problem.atom_types` gives each atom's Lean type, and `domain` lists the
  conditions the expressions need (`y ≠ 0` for a denominator, `0 ≤ u` for a
  `sqrt`, `0 < v` for a `log`), with the hypothesis that discharges each one.
- **Emitters** (all return Lean text that re-parses):
  - `polynomial`, `rational`, `term`, `tactic`, `hyp`, `fresh_name`;
  - `combination`, `linear_combination`, `sq_nonneg`, `mul_nonneg`, `mul_pos`;
  - `nlinarith`, `positivity`, `field_simp`, `norm_num`, `decide`;
  - `rewrite_by`, `calc_chain`, `by_cases`, `rcases`, `witness`;
  - `negate_goal`, `refute`, `sum_by_induction`, `steps`;
  - symbolic: `symbolic` (a Sage expression as a Lean term, functions
    dispatched on the atoms' types), `matrix_term` (`!![…]`),
    `field_simp_clearing` (passes every denominator fact),
    `lemma_rewrite` (a named lemma with its side conditions), and
    `require_domain` (discharge domain conditions, or fail naming them).
- **Solvers:** `solve_exact_lp` (exact rational LP) and `sos_decomposition`
  (exact SOS from a numeric SDP).
- **Sage itself:** everything in `sage.all` (`factor`, `lift`, `solve`,
  `matrix`, `real_roots`, …).

## Rules

- `proof` must be a Lean tactic block (text, or a toolkit `Lean` value).
- `sorry`, `native_decide` and any non-standard axiom are rejected.
- Never commit a `sage_run` call: commit the emitted replacement.
- If no primitive or emitter can express the certificate, report
  `blocked-missing-building-block` and name what is missing.
