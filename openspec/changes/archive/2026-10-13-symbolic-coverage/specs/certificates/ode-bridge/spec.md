# Spec Delta

## Purpose

Lets scripts solve explicit ordinary differential equations in Sage and prove in Lean that the solution found satisfies the equation and its initial conditions, by differentiation rather than by trusting the solver.

## ADDED Requirements

### Requirement: ODE goals translate
Extraction SHALL recognize an ODE goal or hypothesis, written with `deriv` (iterated for higher order), `HasDerivAt` or a notation mapped by a library pack or project entry (such as Physlib's `∂ₜ`, in the `physlib` pack), as a relation between an unknown function and its derivatives. Scripts SHALL see:
- the unknown function;
- the independent variable;
- the equation as a Sage expression in a symbolic function;
- the initial conditions stated as hypotheses or conjuncts.

#### Scenario: Second-order linear equation
- **WHEN** the goal is `∀ t, deriv (deriv x) t + ω ^ 2 * x t = 0` with `x` given explicitly as `fun t => A * Real.cos (ω * t) + B * Real.sin (ω * t)`
- **THEN** the script sees the equation `diff(x(t), t, 2) + ω^2*x(t) == 0` and the explicit `x`

### Requirement: Solutions checked by substitution
The toolkit SHALL build a proof that an explicit function satisfies an ODE: derivative proof terms for each order, rewriting `deriv` with them, and closing the residual identity by `ring_nf`, `field_simp` or `norm_num`. Initial conditions SHALL be checked by evaluation. A solution Sage finds that does not satisfy the equation in Lean SHALL fail with Lean's residual goal shown.

#### Scenario: Harmonic oscillator solution
- **WHEN** a script solves `x'' + ω² x = 0` with `x(0) = x₀` and `x'(0) = v₀` using Sage's `desolve`
- **THEN** the emitted proof shows that `fun t => x₀ * Real.cos (ω * t) + v₀ / ω * Real.sin (ω * t)` satisfies the equation and both conditions, given `hω : ω ≠ 0`

### Requirement: ODE recipe
The recipe set SHALL include an `ode_solution` recipe for ODE goals with an explicit or existentially requested solution. It covers finding the solution in Sage, the substitution proof, and the failure modes: no closed form, a solution valid only on a subinterval, and missing nonzero conditions.

#### Scenario: Existential solution
- **WHEN** the goal is `∃ x : ℝ → ℝ, (∀ t, deriv x t = 2 * x t) ∧ x 0 = 3`
- **THEN** the `ode_solution` template provides `fun t => 3 * Real.exp (2 * t)` and proves both conjuncts
