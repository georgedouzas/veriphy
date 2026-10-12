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
