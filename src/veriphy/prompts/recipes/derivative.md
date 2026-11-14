# Derivative at a point

## When to use

- The goal is `deriv (fun x => f x) a = v`, with `f` built from powers, `exp`, `log`, `sqrt`, `sin`, `cos`, products
  and quotients, and Veriphy translates the derivative (`#veriphy_translate` shows `diff(…)`).
- Sage differentiates and checks the claimed value. The toolkit composes mathlib's derivative lemmas into a
  `HasDerivAt` proof at the point, states Sage's value, and `deriv` follows from it.
- Each quotient, `log`, `sqrt` or real power needs its argument nonzero at the point: a hypothesis stating it, or
  a tactic in `PROOFS`.

## Template

Copy it to the project's `.veriphy/certificates/derivative.sage` (or a more specific name), adapt the lines marked
`EDIT`, keep the header, and run it with `sage_run file "<name>.sage"`.

```sage
# name: derivative
# technique: derivative at a point, by composed HasDerivAt lemmas, with Sage's value
# goal: deriv (fun x => f x) a = v, f built from the coverage list (powers, exp, log, sqrt, sin, cos, quotients)
# description: Sage differentiates; mathlib's derivative lemmas, composed, prove HasDerivAt at the point; deriv follows.
PROOFS = {}  # EDIT: tactics proving the nonzero conditions no hypothesis states, by their Lean text
assert problem.derivatives, 'the goal has no derivative Veriphy translates; inspect it with #veriphy_translate'
d = problem.derivatives[0]
value = diff(d.body, d.var).subs({d.var: d.point})
assert bool(goal.expr.simplify_full() == 0), f'Sage computes the derivative as {value}, not the stated value'
proof = steps(
    has_deriv_at_proof(d.body, d.var, d.point, value, problem, proofs=PROOFS, function=d.function, at=d.at),
    tactic('exact hd.deriv.trans (by first | rfl | ring1 | (field_simp; ring1) | norm_num)'),
)
```

## Worked example

```lean
example : deriv (fun x : ℝ => x ^ 2 * Real.exp x) 1 = 3 * Real.exp 1 := by
  sage_run file "derivative.sage"
-- replacement:
--   have hd : HasDerivAt (fun x => x ^ 2 * Real.exp x) ((3 * (Real.exp 1) : ℝ)) (1) := by
--     convert (((hasDerivAt_id' (1 : ℝ)).pow 2).mul ((hasDerivAt_id' (1 : ℝ)).exp)) using 1
--     all_goals (simp only [Pi.pow_apply]; ring1)
--   exact hd.deriv.trans (by rfl)
```

## Failure modes

- **"the goal has no derivative Veriphy translates":** the function uses something outside the translation (a
  named function, an opaque constant). Unfold it, or add a translation entry for the function it uses.
- **"Sage computes the derivative as …":** the stated value is wrong. The message shows Sage's value.
- **"the derivative needs 'a ≠ 0'":** a quotient, `log` or `sqrt` needs its argument nonzero at the point. Add the
  hypothesis, or put a proof in `PROOFS`.
- **"no derivative lemma for 'tan'":** the function has no composition lemma in the toolkit yet; rewrite it (for
  example `tan = sin / cos`) or prove that step by hand.
