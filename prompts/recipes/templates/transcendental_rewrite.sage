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
