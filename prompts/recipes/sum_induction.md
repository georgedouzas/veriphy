# Sums by induction

## When to use

- The sum runs over `Finset.range n`, `Finset.Icc 1 n`, or `Finset.Ico 0 n` / `Finset.Ico 1 n`. A sum starting
  elsewhere is first rewritten with `Finset.sum_Ico_eq_sum_range`.

- The goal is `∑ k ∈ Finset.range n, f k = F n`, over a field (state ℕ sums over ℚ with casts).
- Sage finds `F`: in a script, `sum(SR('k^2'), var('k'), 0, var('n') - 1).expand()`, printed for you to state the goal.

## Template

Copy it to the project's `.veriphy/certificates/sum_induction.sage` (or a more specific name), adapt the lines marked `EDIT`, keep the header, and run it with `sage_run file "<name>.sage"`.

```sage
# name: sum_induction
# technique: closed-form sum by induction
# goal: ∑ k ∈ Finset.range n, f k = F n (or over Finset.Icc 1 n, Finset.Ico 1 n), with the closed form F stated
# description: Induction on n; both cases close by push_cast and ring1. Sage only finds F (see the recipe).
import re
found = re.search(r'Finset\.(range|Icc|Ico) (?:(\d+) )?(\w+)', goal.text if goal is not None else '')
assert found, 'the goal must be a sum over Finset.range n, Finset.Icc a n or Finset.Ico a n'
index_set, lower, n = found.group(1), int(found.group(2) or 0), found.group(3)
proof = sum_by_induction(n, index_set, lower)
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
