# Definite integrals

## When to use

- The goal is `∫ x in a..b, f x = v` with an elementary integrand: polynomials, `exp`, `log`, `sin`, `cos`, `sqrt` and
  powers, and bounds Sage can evaluate (numerals, multiples of `Real.pi`).
- Sage integrates `f` symbolically, checks that the antiderivative `F` differentiates back to `f`, and that
  `F b - F a = v`. Lean proves `HasDerivAt F (f x) x` on the interval from mathlib's derivative lemmas, applies
  `intervalIntegral.integral_eq_sub_of_hasDerivAt` (continuity of `f` by `fun_prop`), and evaluates `F b - F a`.
- `sin` and `cos` at integer multiples of `π` are stated as facts before the evaluation (`Real.sin_nat_mul_pi`,
  `Real.cos_nat_mul_pi`), since `norm_num` does not evaluate them.

## Template

Copy it to the project's `.veriphy/certificates/definite_integral.sage` (or a more specific name), adapt the lines
marked `EDIT`, keep the header, and run it with `sage_run file "<name>.sage"`.

```sage
# name: definite_integral
# technique: fundamental theorem of calculus with an antiderivative from Sage
# goal: ∫ x in a..b, f x = v, with f elementary (polynomials, exp, log, sin, cos, sqrt, powers)
# description: Sage finds F with F' = f and checks F b - F a = v; Lean proves HasDerivAt F f and evaluates the bounds.
INDEX = 0  # EDIT: which interval integral of the goal, when it has several
proof = definite_integral_proof(problem, INDEX)
```

## Worked examples

```lean
-- the mean of the squared cosine over a period, with the antiderivative φ / 2 + sin (2φ) / 4
example : ∫ φ in (0 : ℝ)..(2 * Real.pi), Real.cos φ ^ 2 = Real.pi := by
  sage_run file "definite_integral.sage"

example : ∫ x in (0 : ℝ)..1, (x ^ 2 + 2 * x) = 4 / 3 := by
  sage_run file "definite_integral.sage"
```

`VeriphyTest/SageRun.lean` also integrates `sin 2φ` over a period.

## Failure modes

- **"the integral is …, not the goal's value":** the stated value is wrong; Sage's value is in the message.
- **"Sage finds no elementary antiderivative":** the integrand has none (`exp (-x²)`), or Sage needs help; split
  the integral, or substitute (`intervalIntegral.integral_comp_mul_left`) before the template.
- **"the goal has no interval integral the translation could read":** the integral is over a set or a measure, not
  `a..b`, or its integrand has a function outside the tables.
- **The derivative step stays open:** the integrand needs an identity to match its antiderivative's derivative beyond
  the power-reduction and double-angle formulas; prove `HasDerivAt` by hand with `has_deriv_at`.
- **The value step stays open:** a trigonometric value at a non-integer multiple of `π` (`sin (π / 3)`); state it as
  a fact (`Real.sin_pi_div_three`) before the template's step.
