# Rational-function inequality

## When to use

- The goal is `lhs ≤ rhs` or `lhs < rhs` and either side has a division: bounds such as `x / (x ^ 2 + 1) ≤ 1 / 2`, efficiencies, ratios of energies.
- Sage writes `rhs - lhs` as a single fraction `N / D` (`goal.expr` is the symbolic `lhs - rhs`). Lean then proves `0 < D`, proves `0 ≤ N` by squares, checks `rhs - lhs = N / D` with `field_simp; ring`, and concludes with `div_nonneg`.
- Denominators that need a hypothesis (`0 < y`) are listed in `problem.domain`. Set `D_PROOF` to a tactic that uses it, for example `positivity` does not see hypotheses but `nlinarith [hy]` or `exact mul_pos hy hy` do.

## Template

Copy it to the project's `.veriphy/certificates/rational_inequality.sage` (or a more specific name), adapt the lines marked `EDIT`, keep the header, and run it with `sage_run file "<name>.sage"`.

```sage
# name: rational_inequality
# technique: clear denominators, then a sum of squares on the numerator
# goal: lhs ≤ rhs or lhs < rhs, with rational functions of real or rational atoms
# description: Write rhs - lhs = N / D in Sage with D > 0; prove 0 ≤ N by squares and conclude by div_nonneg.
D_PROOF = 'positivity'  # EDIT: a tactic proving 0 < D, when positivity cannot (for example `nlinarith [hy]`)
HINTS = []  # EDIT: candidate squares for N, as in the sos recipe, when N has real zeros
e = -goal.expr  # rhs - lhs, as a symbolic rational function
num, den = e.numerator_denominator()
if bool(den.subs({v: 0 for v in den.variables()}) < 0) if den.variables() else bool(den < 0):
    num, den = -num, -den  # normalize the sign so that D is positive at the origin
N = R(num.expand())

def squares_of(p):
    # p = c₀ + Σ cᵢ qᵢ² with cᵢ ≥ 0: hinted squares by an exact LP, otherwise the SDP route
    if not HINTS:
        return sos_decomposition(p)
    sq = [R(1)] + [R(h) ** 2 for h in HINTS]
    mons = sorted(set().union(*[set(q.monomials()) for q in sq]) | set(p.monomials()))
    rows = [([q.monomial_coefficient(mn) for q in sq], p.monomial_coefficient(mn)) for mn in mons]
    w = solve_exact_lp(len(sq), eqs=rows, objective=[1] * len(sq), nonneg=True)
    return None if w is None else [(c, q) for c, q in zip(w, [R(1)] + [R(h) for h in HINTS]) if c != 0]

squares = squares_of(N)
assert squares is not None, f'no sum of squares for the numerator {N}; supply candidate squares in HINTS'
strict = goal.rel == 'lt'
assert not strict or N.constant_coefficient() > 0 or any(c > 0 and q.degree() == 0 for c, q in squares), \
    'a strict goal needs a positive constant in the numerator; use hint_search'
n_text, d_text = polynomial(N, problem), symbolic(den, problem)
proof = steps(
    tactic(f'have hD : 0 < {d_text} := by {D_PROOF}'),
    tactic(f'have hN : 0 {"<" if strict else "≤"} {n_text} := by nlinarith [{", ".join(str(sq_nonneg(q, problem)) for c, q in squares if q.degree() > 0)}]'),
    tactic(f'have key : {rhs.text} - ({lhs.text}) = {parenthesize(str(n_text))} / {parenthesize(str(d_text))} := by\n  field_simp\n  ring'),
    tactic(f'rw [← {"sub_pos" if strict else "sub_nonneg"}, key]'),
    tactic(f'exact {"div_pos hN hD" if strict else "div_nonneg hN hD.le"}'),
)
```

## Worked example

```lean
example (x : ℝ) : x / (x ^ 2 + 1) ≤ 1 / 2 := by
  sage_run file "rational_inequality.sage"
-- replacement:
--   have hD : 0 < 2 * (x ^ 2) + 2 := by positivity
--   have hN : 0 ≤ x ^ 2 - 2 * x + 1 := by nlinarith [sq_nonneg (-x + 1)]
--   have key : 1 / 2 - (x / (x ^ 2 + 1)) = (x ^ 2 - 2 * x + 1) / (2 * (x ^ 2) + 2) := by
--     field_simp
--     ring
--   rw [← sub_nonneg, key]
--   exact div_nonneg hN hD.le
```

## Failure modes

- **"no sum of squares for the numerator":** the numerator has real zeros (the SDP sits on the boundary) or is not a sum of squares. Put the expected squares in `HINTS`, or use `hint_search` on the numerator.
- **`positivity` fails on `0 < D`:** the denominator's sign comes from a hypothesis. Set `D_PROOF`, for example `nlinarith [hy]`.
- **`field_simp; ring` fails on `key`:** a denominator is not known to be nonzero. `field_simp` needs a fact for each one; add `have` facts first (see `field_simp_clearing` in `prompts/certify.md`).
- **A strict goal:** the numerator must be strictly positive. The template asserts a positive constant; otherwise use `hint_search` with `nlinarith`.
