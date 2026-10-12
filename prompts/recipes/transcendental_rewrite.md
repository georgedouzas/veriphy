# Transcendental rewrite

## When to use

- The goal is an identity between `Real.exp`, `Real.log`, `Real.sqrt`, `Real.sin`, `Real.cos` expressions that a short chain of named mathlib lemmas proves: `exp_add`, `sin_sq_add_cos_sq`, `log_mul`, `sqrt_mul_self`.
- Sage confirms the identity first (`goal.expr` simplifies to 0), so a false statement is caught before any Lean is written.
- `lemma_rewrite` passes each side condition (`x ≠ 0`, `0 ≤ u`) as the hypothesis that states it, or as `(by <tactic>)` from `proofs`, and fails naming any condition it cannot discharge.

## Template

Copy it to the project's `.veriphy/certificates/transcendental_rewrite.sage` (or a more specific name), adapt the lines marked `EDIT`, keep the header, and run it with `sage_run file "<name>.sage"`.

```sage
# name: transcendental_rewrite
# technique: rewrite with named mathlib lemmas from the translation tables, checked in Sage first
# goal: an identity between exp, log, sqrt, sin, cos, cosh, sinh expressions
# description: Sage confirms the identity, then a rewrite the tables offer (core, packs, project) closes it.
# EDIT: the rewrites, as (lemma, right-to-left, side conditions); left empty, the tables' first candidate is used
REWRITES = []
PROOFS = {}  # EDIT: tactics proving side conditions no hypothesis states, by their Lean text
CLOSE = None  # EDIT: a tactic closing what remains after the rewrites (for example 'ring'), or None

e = goal.expr
assert e is not None, 'the goal has no symbolic form; check the problem with print(goal)'
assert bool(e.simplify_full().canonicalize_radical() == 0) or bool(e.simplify_exp().simplify_trig() == 0), \
    f'Sage cannot confirm the identity: lhs - rhs simplifies to {e.simplify_full()}'
if REWRITES:
    blocks = [lemma_rewrite(lemma, problem, reverse=rev, side=side, proofs=PROOFS) for lemma, rev, side in REWRITES]
else:
    candidates = rewrite_candidates(problem)
    assert candidates, (f'no rewrite in the tables applies to {goal.text}; list one in REWRITES, '
                        'or add a rewrite entry to .veriphy/translations/')
    blocks = [candidates[0].emit(problem, proofs=PROOFS)]
proof = steps(*blocks, tactic(CLOSE)) if CLOSE else steps(*blocks)
```

## Worked example

```lean
example (a b : ℝ) : Real.exp a * Real.exp b = Real.exp (a + b) := by
  sage_run file "transcendental_rewrite.sage"
-- replacement: rw [← Real.exp_add]

example (x : ℝ) : Real.sin x ^ 2 + Real.cos x ^ 2 = 1 := by
  sage_run file "transcendental_rewrite.sage"
-- replacement: rw [Real.sin_sq_add_cos_sq]
```

## Failure modes

- **"Sage cannot confirm the identity":** the statement is false, or it holds only under conditions Sage does not assume (branch cuts, signs). Check the statement numerically; for conditional identities, list the rewrites and their side conditions in `REWRITES`.
- **"no rewrite in the tables applies":** list the rewrites in `REWRITES`, as `(lemma, right_to_left, [side conditions])`, or add a rewrite entry to the project's `.veriphy/translations/` so that every later goal of this shape finds it. Find lemma names with `exact?` or the mathlib docs.
- **"side condition … is not stated":** add the hypothesis, or prove it in place with `PROOFS = {'0 < x': 'positivity'}`.
- **The rewrite leaves a goal:** set `CLOSE` to the tactic that finishes it (`ring`, `field_simp`, `norm_num`).
