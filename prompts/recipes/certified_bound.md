# Certified bounds

## When to use

- The goal bounds a transcendental value at an explicit rational point by a decimal: `Real.exp 1 < 2.7183`,
  `3.14159 < Real.pi`, `Real.log (3 / 2) < 0.4055`, `Real.sin c`, `Real.cos c`.
- Sage's interval arithmetic checks the bound and picks the cheapest certificate: one of mathlib's decimal lemmas
  (`Real.pi_gt_d6`, `Real.exp_one_lt_d9`, …) when it implies the bound, otherwise mathlib's series bound with the
  least truncation order whose rational remainder fits (`Real.exp_bound`, `Real.abs_log_sub_add_sum_range_le`,
  `Real.sin_bound`, `Real.cos_bound`). Lean checks the truncated sum and the remainder exactly (`norm_num`,
  `linarith`): no floating point reaches the proof.

## Template

Copy it to the project's `.veriphy/certificates/certified_bound.sage` (or a more specific name), adapt it, keep the
header, and run it with `sage_run file "<name>.sage"`. It reads the function, point and bound from the goal.

```sage
# name: certified_bound
# technique: rational bounds on transcendental values from mathlib's decimal lemmas or truncated series
# goal: Real.exp c < b, b < Real.pi, Real.log c < b and the like, for explicit rationals c and b
# description: Sage's interval arithmetic picks the lemma or the truncation order; Lean checks the rational remainder.
import re
text = goal.text if goal is not None else ''
found = re.search(r'Real\.(\w+)\s*\(?\s*([-0-9./ ]*?)\s*\)?\s*(<|>)\s*([0-9.]+)$', text) or \
    re.search(r'^([0-9.]+)\s*(<|>)\s*Real\.(\w+)\s*\(?\s*([-0-9./ ]*?)\s*\)?$', text)
assert found, f'the goal must compare Real.f c with a decimal: {text}'
if text.startswith('Real.'):
    function, point, relation, bound = found.groups()
    upper = relation == '<'
else:
    bound, relation, function, point = found.groups()
    upper = relation == '>'
point = QQ(sage_eval(point)) if point.strip() else QQ(0)
proof = bound_proof(function.lower(), point, QQ(Integer(bound.replace('.', ''))) / 10 ** len(bound.partition('.')[2]), upper=upper)
```

## Worked examples

```lean
example : Real.exp 1 < 2.7183 := by
  sage_run file "certified_bound.sage"
-- replacement: exact lt_trans Real.exp_one_lt_d9 (by norm_num)

example : Real.exp (1 / 2) < 1.6488 := by
  sage_run file "certified_bound.sage"
-- replacement: the series to order 6, with its remainder, then linarith
```

## Failure modes

- **"no remainder bound is available for gamma in mathlib":** only `exp`, `log`, `sin`, `cos` and `π` have series
  bounds in mathlib; a bound on `Real.Gamma (1/3)` is refused rather than emitted unchecked.
- **"the bound fails or is too tight":** the message shows Sage's enclosure of the value; loosen the bound.
- **A point too far out** (`|c| > 1` for `exp`, `sin`, `cos`; `c ∉ (0, 2)` for `log`): the series lemma does not apply;
  reduce the argument first (`exp (2 c) = exp c ^ 2`, `log (a b) = log a + log b`).
- **"no truncation up to order 60":** the point is too close to the series' singularity (`log` near 0 or 2).
