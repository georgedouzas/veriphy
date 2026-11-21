# Ideal membership

## When to use

- The goal is a polynomial equality `lhs = rhs`.
- It follows from polynomial *equality* hypotheses by algebra alone: substituting, eliminating, combining.
- Also covers kernel-span facts ("every solution of these linear equations is a combination of these vectors").

## Template

Copy it to the project's `.veriphy/certificates/ideal_membership.sage` (or a more specific name), adapt the lines marked `EDIT`, keep its `SCRIPT` declaration, and run it with `veriphy certify "<name>.sage"`.

```sage
SCRIPT = {
    'name': 'ideal_membership',
    'serves': 'certify',
    'technique': 'ideal membership (Gröbner cofactors)',
    'goal': 'lhs = rhs, implied by polynomial equality hypotheses',
    'description': 'Write lhs - rhs as a combination of the equality hypotheses; linear_combination checks it.',
    'inputs': {},
}


def run(goal, inputs):
    eqs = [h for h in hyps if h.rel == 'eq' and h.poly is not None]
    assert goal is not None and goal.rel == 'eq', 'the goal must be a polynomial equality'
    assert eqs, 'no polynomial equality hypotheses to combine'
    assert goal.poly in R.ideal([h.poly for h in eqs]), 'the goal does not follow from the equalities (not in the ideal)'
    cofactors = goal.poly.lift(R.ideal([h.poly for h in eqs]))
    proof = linear_combination([(c, hyp(problem, h.name)) for c, h in zip(cofactors, eqs)], problem)
    return found(proof)
```

## Worked example

```lean
example (a b : ℝ) (h : a + b = 3) (h' : a * b = 2) : a ^ 2 + b ^ 2 = 5 := by
  veriphy certify "ideal_membership.sage"
-- replacement: linear_combination (a + b + 3) * h + (-2) * h'
```

## Failure modes

- **"the goal does not follow from the equalities (not in the ideal)":** an inequality or a non-polynomial fact is needed. Check the hypothesis list the script prints; try `farkas` or `hint_search`.
- **"no polynomial equality hypotheses":** the needed fact is an inequality, or is hidden in a definition. Unfold it first (`simp only [...]`), then rerun.
- **`linear_combination` fails in Lean:** an atom was read differently from what you expect (for example `↑n` against `n`). Print `atoms` and normalize the casts first (`push_cast at *`).
