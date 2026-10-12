# Transcendental rewrite

## When to use

- The goal is an identity between `Real.exp`, `Real.log`, `Real.sqrt`, `Real.sin`, `Real.cos` expressions that a short chain of named mathlib lemmas proves: `exp_add`, `sin_sq_add_cos_sq`, `log_mul`, `sqrt_mul_self`.
- Sage confirms the identity first (`goal.expr` simplifies to 0), so a false statement is caught before any Lean is written.
- `lemma_rewrite` passes each side condition (`x ≠ 0`, `0 ≤ u`) as the hypothesis that states it, or as `(by <tactic>)` from `proofs`, and fails naming any condition it cannot discharge.

## Template

Copy it to the project's `certificates/transcendental_rewrite.sage` (or a more specific name), adapt the lines marked `EDIT`, keep the header, and run it with `sage_run file "certificates/<name>.sage"`.

```sage
# name: transcendental_rewrite
# technique: rewrite chain with named mathlib lemmas, checked in Sage first
# goal: an identity between exp, log, sqrt, sin, cos expressions
# description: Sage confirms the identity, then rewrites by named lemmas (side conditions from the hypotheses) close it.
# EDIT: the rewrites, as (lemma, right-to-left, side conditions); left empty, they are chosen from TABLE
import re
REWRITES = []
CLOSE = None  # EDIT: a tactic closing what remains after the rewrites (for example 'ring'), or None

# lemma choices, first match wins: (functions the goal must use, rewrites as (lemma, right-to-left, side conditions))
TABLE = [
    ({'sin', 'cos'}, [('Real.sin_sq_add_cos_sq', False, [])]),
    ({'exp'}, [('Real.exp_add', True, [])]),
]
e = goal.expr
assert e is not None, 'the goal has no symbolic form; check the problem with print(goal)'
assert bool(e.simplify_full().canonicalize_radical() == 0) or bool(e.simplify_exp().simplify_trig() == 0), \
    f'Sage cannot confirm the identity: lhs - rhs simplifies to {e.simplify_full()}'
# the functions the Lean goal uses (Sage has already simplified its own copy, so read the text)
used = set(re.findall(r'(?:Real|Complex)\.(\w+)', goal.text))
rewrites = REWRITES or next((rs for needed, rs in TABLE if needed <= used), [])
assert rewrites, f'no table lemma applies to {goal.text}; list the rewrites in REWRITES'
blocks = [lemma_rewrite(lemma, problem, reverse=rev, side=side) for lemma, rev, side in rewrites]
proof = steps(*blocks, tactic(CLOSE)) if CLOSE else steps(*blocks)
```

## Worked example

```lean
example (a b : ℝ) : Real.exp a * Real.exp b = Real.exp (a + b) := by
  sage_run file "certificates/transcendental_rewrite.sage"
-- replacement: rw [← Real.exp_add]

example (x : ℝ) : Real.sin x ^ 2 + Real.cos x ^ 2 = 1 := by
  sage_run file "certificates/transcendental_rewrite.sage"
-- replacement: rw [Real.sin_sq_add_cos_sq]
```

## Failure modes

- **"Sage cannot confirm the identity":** the statement is false, or it holds only under conditions Sage does not assume (branch cuts, signs). Check the statement numerically; for conditional identities, list the rewrites and their side conditions in `REWRITES`.
- **"no table lemma applies":** list the rewrites in `REWRITES`, as `(lemma, right_to_left, [side conditions])`. Find lemma names with `exact?` or the mathlib docs.
- **"side condition … is not stated":** add the hypothesis, or prove it in place with `proofs={'0 < x': 'positivity'}` in `lemma_rewrite`.
- **The rewrite leaves a goal:** set `CLOSE` to the tactic that finishes it (`ring`, `field_simp`, `norm_num`).
