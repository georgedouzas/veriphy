# name: factor_rewrite
# technique: factorization rewrite
# goal: lhs = rhs, to continue from the factored form of lhs
# description: Rewrite lhs to its factored form (certified by ring1); leaves factored = rhs open, so follow it with a tactic.
assert lhs is not None, 'the goal must be a polynomial equality lhs = rhs'
unit, factors = QQ(lhs.poly.factor().unit()), list(lhs.poly.factor())
parts = [f'({polynomial(f, problem)})' + (f' ^ {m}' if m > 1 else '') for f, m in factors]
factored = ' * '.join(parts) or str(rational(unit))
if parts and unit != 1:
    factored = f'{rational(unit)} * ({factored})' if unit != -1 else f'-({factored})'
proof = tactic(f'refine Eq.trans (show {lhs.text} = {factored} by ring1) ?_')
