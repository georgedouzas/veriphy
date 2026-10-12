# Sums by induction

## When to use

- The goal is `∑ k ∈ Finset.range n, f k = F n`, over a field (state ℕ sums over ℚ with casts).
- Sage finds `F`: in a script, `sum(SR('k^2'), var('k'), 0, var('n') - 1).expand()`, printed for you to state the goal.

## Template

Copy it to the project's `.veriphy/certificates/sum_induction.sage` (or a more specific name), adapt the lines marked `EDIT`, keep the header, and run it with `sage_run file "<name>.sage"`.

```sage
# name: sum_induction
# technique: closed-form sum by induction
# goal: ∑ k ∈ Finset.range n, f k = F n, with the closed form F already stated
# description: Induction on n; both cases close by push_cast and ring1. Sage only finds F (see the recipe).
import re
found = re.search(r'Finset\.range (\w+)', goal.text if goal is not None else '')
assert found, 'the goal must be a sum over Finset.range n'
proof = sum_by_induction(found.group(1))
```

## Worked example

```lean
example (n : ℕ) :
    ∑ k ∈ Finset.range n, (k : ℚ) ^ 2 = (n : ℚ) ^ 3 / 3 - (n : ℚ) ^ 2 / 2 + (n : ℚ) / 6 := by
  sage_run file "sum_induction.sage"
```

## Failure modes

- **`ring1` fails in a case:** the stated closed form is wrong. Recompute it in Sage and compare.
- **The sum is not over `Finset.range n`:** reindex first (`Finset.sum_range_succ`, `Finset.range_eq_Ico`), or adapt the emitted induction.
