# name: farkas
# technique: farkas
# goal: False from linear hypotheses (=, ≤, <) over an ordered field
# description: Refute a linear system with exact Farkas multipliers found by an LP.
n = len(hyps)
usable = [h.poly is not None and h.rel in ('eq', 'le', 'lt') and h.poly.degree() <= 1 for h in hyps]
forms = [h.poly if ok else R(0) for h, ok in zip(hyps, usable)]
rows = [([QQ(int(j == i)) for j in range(n)], 0) for i in range(n) if not usable[i]]
rows += [([f.monomial_coefficient(x) for f in forms], 0) for x in R.gens()]
kappa = [f.constant_coefficient() for f in forms]
nonneg = [i for i, h in enumerate(hyps) if h.rel in ('le', 'lt')]
weights = solve_exact_lp(n, eqs=rows, les=[([-k for k in kappa], 1)], objective=[1] * n, nonneg=nonneg)
if weights is None:
    strict = [1 if h.rel == 'lt' else 0 for h in hyps]
    weights = solve_exact_lp(n, eqs=rows + [(kappa, 0)], les=[([-s for s in strict], 1)], objective=[1] * n, nonneg=nonneg)
assert weights is not None, 'the hypotheses are consistent: no Farkas certificate'
constant = sum(w * k for w, k in zip(weights, kappa))
uses_strict = any(w != 0 and h.rel == 'lt' for w, h in zip(weights, hyps))
proof = refute(constant, strict=uses_strict, weighted=[(w, hyp(problem, h.name)) for w, h in zip(weights, hyps)], problem=problem)
