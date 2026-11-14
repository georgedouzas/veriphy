# name: hint_search
# technique: nlinarith hint search (squares chosen by an exact LP)
# goal: an inequality that nlinarith proves once it is given the right squares
# description: Pick squares whose nonnegative combination, plus the hypotheses, gives the goal; nlinarith checks.
MAX_CANDIDATES = 60  # EDIT: raise to search more squares
target = -goal.poly  # the goal a ≤ b becomes 0 ≤ b - a
gens = list(R.gens())
candidates = set(gens)
candidates |= {g + s * h for g in gens for h in gens for s in (1, -1) if g != h}
candidates |= {g * h + s for g in gens for h in gens for s in (1, -1)}
candidates |= {g + s for g in gens for s in (1, -1)}
squares = sorted(candidates, key=str)[:MAX_CANDIDATES]
nonneg = [-h.poly for h in hyps if h.poly is not None and h.rel in ('le', 'lt')]
forms = [q**2 for q in squares] + nonneg + [a * b for a in nonneg for b in nonneg]
mons = sorted(set().union(set(target.monomials()), *[set(f.monomials()) for f in forms]))
rows = [([f.monomial_coefficient(m) for f in forms], -target.monomial_coefficient(m)) for m in mons if m != 1]
slack = ([f.constant_coefficient() for f in forms], -target.constant_coefficient())
weights = solve_exact_lp(len(forms), eqs=rows, les=[slack], objective=[1] * len(forms), nonneg=True)
assert weights is not None, 'no combination of the candidate squares and hypothesis products gives the goal'
proof = nlinarith([sq_nonneg(q, problem) for q, w in zip(squares, weights) if w != 0])
