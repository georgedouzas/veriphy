# ODE solutions

## When to use

- The goal is an ordinary differential equation in an unknown function `x : ℝ → ℝ`, written with `deriv`
  (iterated for higher orders), and either
  - a hypothesis `hx : x = fun s => …` gives `x` explicitly, or
  - the goal asks for a solution: `∃ x : ℝ → ℝ, (∀ t, ODE) ∧ x t₀ = y₀ ∧ deriv x t₀ = y₁ …`.
- `#veriphy_translate` shows the equation with `F_x(t)` and `diff(F_x(s_), s_, k)`; a Physlib `∂ₜ` translates the
  same way when the `physlib` pack is active.
- Sage is not trusted with the solution. Its `desolve` (with the initial conditions) only proposes the witness. The
  proof states each derivative of the solution as a fact `dₖ : deriv (fun s => Bₖ₋₁) = fun s => Bₖ`, proved by
  composed `HasDerivAt` lemmas, rewrites the equation with them, and closes the identity by `ring1` or `field_simp`.
  The initial conditions close by `norm_num` with the same facts.

## Template

Copy it to the project's `.veriphy/certificates/ode_solution.sage` (or a more specific name), adapt the lines marked
`EDIT`, keep the header, and run it with `sage_run file "<name>.sage"`.

```sage
# name: ode_solution
# technique: ODE solution checked by differentiation
# goal: an equation in deriv x with x defined by a hypothesis `hx : x = fun s => …`, or ∃ x, (∀ t, ODE) ∧ conditions
# description: Sage solves (desolve) or takes the stated x; derivative facts, rewriting and ring/field_simp check it.
PROOFS = {}  # EDIT: tactics proving the nonzero conditions no hypothesis states, by their Lean text
SOLUTION = None  # EDIT: a solution body in s_ (e.g. 3 * exp(2 * SR.var('s_'))) when Sage finds none
if problem.exists_function is not None:
    proof = solve_exists(problem, proofs=PROOFS, solution=SOLUTION)
else:
    proof = verify_definition(problem, proofs=PROOFS)
```

## Worked examples

```lean
example : ∃ x : ℝ → ℝ, (∀ t, deriv x t = 2 * x t) ∧ x 0 = 3 := by
  sage_run file "ode_solution.sage"
-- replacement:
--   have d1 : deriv (fun s => 3 * (Real.exp (2 * s))) = fun s => 6 * (Real.exp (2 * s)) := by
--     funext s
--     have hd : HasDerivAt (fun s => 3 * (Real.exp (2 * s))) ((6 * (Real.exp (2 * s)) : ℝ)) (s) := by
--       convert ((((hasDerivAt_id' (s : ℝ)).const_mul (2 : ℝ)).exp).const_mul (3 : ℝ)) using 1
--       all_goals (ring1)
--     exact hd.deriv
--   exact ⟨fun s => 3 * (Real.exp (2 * s)), fun t => by (simp only [d1]; ring1), by (norm_num [d1]; done)⟩

example (ω x₀ v₀ : ℝ) (hω : ω ≠ 0) :
    ∃ x : ℝ → ℝ, (∀ t, deriv (deriv x) t + ω ^ 2 * x t = 0) ∧ x 0 = x₀ ∧ deriv x 0 = v₀ := by
  sage_run file "ode_solution.sage"
-- the witness is fun s => x₀ * Real.cos (s * ω) + v₀ * Real.sin (s * ω) / ω; `hω` lets field_simp clear 1/ω
```

## Failure modes

- **A residual goal such as `Real.exp (t * 3) * 9 = Real.exp (t * 3) * 6`:** the solution does not satisfy the
  equation. Lean shows the equation after rewriting with the derivative facts and normalizing. Check `SOLUTION`, or
  the equation Sage solved (print `problem.exists_function`).
- **No closed form:** `desolve` raises, or returns an implicit or integral form. The template cannot proceed; state a
  solution in `SOLUTION` if one is known (a series truncation does not solve the equation), or prove the goal with
  mathlib's existence theorems (`IsPicardLindelof`) instead.
- **A solution valid only on a subinterval** (`log s`, `sqrt s`, `1 / s`): the derivative facts are stated at every
  point, so the toolkit fails naming the condition (`the derivative needs 's ≠ 0'`). State the equation on the
  interval (`∀ t > 0, …`) and prove it pointwise with the `derivative` recipe, or choose a solution defined on all
  of ℝ.
- **A missing nonzero condition** (`the derivative needs 'ω ≠ 0'`, or `field_simp` leaving a division): add the
  hypothesis to the goal, or a proof to `PROOFS`. Sage's `desolve` divides by parameters it assumes nonzero; the
  problem's `≠ 0` and sign hypotheses are passed to it as assumptions.
- **"no hypothesis `x = fun s => …` defines a function of the goal":** the definition is not a hypothesis
  `x = fun s => …`. Rewrite `x`'s definition into that form (`funext`), or `subst` it first.
