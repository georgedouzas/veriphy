# Infeasibility certificates

## When to use

- The goal is `False` from **nonlinear** polynomial hypotheses that `farkas` (linear) cannot refute, or `p = 0`
  from equalities that imply only a power of `p`.
- Three certificates, in the order the template tries them:
  - **radical membership** for an equality goal: the least `k` with `(lhs - rhs)ᵏ` in the ideal of the equality
    hypotheses (a Gröbner lift), then `pow_eq_zero_iff`;
  - **Nullstellensatz** when every hypothesis is an equality: `1 = Σ gᵢ fᵢ` from a Gröbner lift, checked by
    `linear_combination`;
  - **Positivstellensatz** otherwise: an exact LP over the inequality hypotheses, their pairwise products, candidate
    squares (each variable, and sums and differences of two) and polynomial multipliers of the equalities, making a
    positive constant out of nonpositive facts. `linear_combination` checks the identity (it accepts inequality facts
    with nonnegative weights).

## Template

Copy it to the project's `.veriphy/certificates/infeasibility.sage` (or a more specific name), adapt the lines marked `EDIT`,
keep the header, and run it with `sage_run file "<name>.sage"`.

```sage
# name: infeasibility
# technique: Nullstellensatz, radical membership and Positivstellensatz certificates
# goal: False from polynomial equalities or real inequalities that farkas cannot refute; or p = 0 from pᵏ in the ideal
# description: Gröbner lifts and an exact LP over products and squares find the certificate; linear_combination checks it.
SQUARES = None  # EDIT: polynomials (in x0, x1, …) whose squares may enter a Positivstellensatz certificate
MULTIPLIER_DEGREE = 1  # EDIT: the degree of the multipliers of the equalities
if goal_kind == 'rel' and goal.rel == 'eq':
    proof = radical_proof(problem)
elif all(h.rel == 'eq' for h in hyps if h.poly is not None):
    proof = nullstellensatz_proof(problem)
else:
    proof = positivstellensatz_proof(problem, squares=SQUARES, multiplier_degree=MULTIPLIER_DEGREE)
```

## Worked examples

```lean
example (x y : ℝ) (h1 : x ^ 2 + y ^ 2 < 1) (h2 : x + y ≥ 2) : False := by
  sage_run file "infeasibility.sage"
-- replacement:
--   have hκ : (1 : ℝ) < 0 := by
--     linear_combination h1 + (2) * h2 + (1 / 2) * mul_nonneg (sub_nonneg.mpr h2) (sub_nonneg.mpr h2) +
--       (1 / 2) * sq_nonneg (x - y)
--   norm_num at hκ

example (x y : ℚ) (hxy : x * y = 1) (hx : x = 0) : False := by
  sage_run file "infeasibility.sage"
-- replacement: have h1 : (1 : ℚ) = 0 := by linear_combination (-1) * hxy + (y) * hx; exact one_ne_zero h1

example (x : ℝ) (h : x ^ 2 = 0) : x = 0 := by
  sage_run file "infeasibility.sage"
```

## Failure modes

- **"the equalities have a common zero over ℂ":** the system is consistent over ℂ; a real contradiction needs the
  Positivstellensatz (add an inequality, or state the goal over ℝ with order hypotheses).
- **"no Positivstellensatz certificate of this degree":** pass squares the argument needs in `SQUARES` (from a
  sketch of the human proof), or raise `MULTIPLIER_DEGREE`. A consistent system has no certificate at all: check the
  statement numerically.
- **"no power up to 8 of the goal is in the ideal":** the goal does not follow from the equalities alone.
