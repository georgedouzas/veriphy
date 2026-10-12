# Case split

## When to use

- The goal is easy on each side of a condition: a sign, a comparison, which root interval.
- Sage helps locate the condition: `p.real_roots()` or `real_root_intervals` give the sign changes.

## Template

Copy it to the project's `certificates/case_split.sage` (or a more specific name), adapt the lines marked `EDIT`, keep the header, and run it with `sage_run file "certificates/<name>.sage"`.

```sage
# name: case_split
# technique: case split
# goal: a statement that is easy on each side of a sign or comparison condition
# description: Split on a condition Sage suggests; each branch gets its own tactic.
condition = term('0 ≤ x')  # EDIT: the split, in the goal's terms (Sage can locate sign changes with real_roots)
name = fresh_name(problem, 'hx')
on_true = tactic(f'exact mul_nonneg {name} {name}')  # EDIT: the branch where the condition holds
on_false = nlinarith()  # EDIT: the branch where it fails
proof = by_cases(name, condition, on_true, on_false)
```

## Worked example

```lean
example (x : ℚ) : 0 ≤ x * x := by
  sage_run file "certificates/case_split.sage"
```

## Failure modes

- **A branch fails:** give that branch its own recipe, for example a `farkas` or `sos` script run inside it as a nested `steps`.
- **More than two cases:** nest `by_cases`, or use `rcases` on a disjunction lemma (`le_or_lt`, `lt_trichotomy`).
