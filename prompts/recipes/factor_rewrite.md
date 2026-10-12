# Factorization rewrite

## When to use

- An equality goal `lhs = rhs` where the next step needs the factored form of `lhs`: roots, signs, cancellation.
- Leaves the goal `factored = rhs` open for the next tactic.

## Template

Copy it to the project's `certificates/factor_rewrite.sage` (or a more specific name), adapt the lines marked `EDIT`, keep the header, and run it with `sage_run file "certificates/<name>.sage"`.

```sage
# name: factor_rewrite
# technique: factorization rewrite
# goal: lhs = rhs, to continue from the factored form of lhs
# description: Replace the goal by factored(lhs) = rhs, the step certified by ring1; leaves that goal open.
assert lhs is not None, 'the goal must be a polynomial equality lhs = rhs'
unit, factors = QQ(lhs.poly.factor().unit()), list(lhs.poly.factor())
parts = [f'({polynomial(f, problem)})' + (f' ^ {m}' if m > 1 else '') for f, m in factors]
factored = ' * '.join(parts) or str(rational(unit))
if parts and unit != 1:
    factored = f'{rational(unit)} * ({factored})' if unit != -1 else f'-({factored})'
proof = tactic(f'refine Eq.trans (show {lhs.text} = {factored} by ring1) ?_')
```

## Worked example

```lean
example (x : ℚ) : x ^ 4 - 1 = (x - 1) * (x + 1) * (x ^ 2 + 1) := by
  sage_run file "certificates/factor_rewrite.sage"
  ring
```

## Failure modes

- **"the goal must be a polynomial equality lhs = rhs":** the goal has no polynomial form. Normalize it first (`field_simp`, `push_cast`).
- **The factored form does not help:** factor over QQ only. Irrational factors need a substitution (see `calc_derivation`).
