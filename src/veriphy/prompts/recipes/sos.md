# Sum of squares

## When to use

- The goal is `0 ≤ p` or `p ≥ 0` with `p` a polynomial: potentials, energies, discriminants.
- Three routes, tried in order:
  1. the factorization (perfect squares, positive-definite quadratics);
  2. a numeric SDP rounded exactly (strictly positive polynomials);
  3. candidate squares you supply in `HINTS` (for example field strengths), solved by an exact LP.

## Template

Copy it to the project's `.veriphy/certificates/sos.sage` (or a more specific name), adapt the lines marked `EDIT`, keep the header, and run it with `sage_run file "<name>.sage"`.

```sage
# name: sos
# technique: sum of squares (factorization, numeric SDP, or hinted squares)
# goal: 0 ≤ p or p ≥ 0, p a polynomial
# description: Write p as Σ cᵢ qᵢ² with rational cᵢ ≥ 0; linear_combination with sq_nonneg terms checks it.
HINTS = []  # EDIT: candidate squares qᵢ (polynomials in x0, x1, ...) when p neither factors nor passes the SDP
p = -goal.poly

def from_factors(p):
    # squares from the factorization: even powers are squares; odd factors must be constants or
    # positive-definite single-variable quadratics (completed square)
    fac = p.factor()
    if fac.unit() < 0:
        return None
    squares = [(QQ(fac.unit()), R(1))]
    for f, m in fac:
        if m % 2 == 0:
            squares = [(c, q * f ** (m // 2)) for c, q in squares]
            continue
        if len(f.variables()) == 1 and f.degree() == 2:
            u = f.univariate_polynomial(); a, b, c0 = QQ(u[2]), QQ(u[1]), QQ(u[0])
            if a > 0 and b**2 - 4*a*c0 < 0:
                x = R(f.variables()[0]); half = f ** (m // 2)
                squares = [(c * d, q * r * half) for c, q in squares for d, r in ((a, x + b/(2*a)), (c0 - b**2/(4*a), R(1)))]
                continue
        return None
    return squares

def from_hints(p, hints):
    # exact LP: p = c₀ + Σ cᵢ hᵢ² with cᵢ ≥ 0
    sq = [R(1)] + [R(h)**2 for h in hints]
    mons = sorted(set().union(*[set(q.monomials()) for q in sq]) | set(p.monomials()))
    rows = [([q.monomial_coefficient(mn) for q in sq], -p.monomial_coefficient(mn)) for mn in mons]
    w = solve_exact_lp(len(sq), eqs=rows, objective=[1] * len(sq), nonneg=True)
    return None if w is None else [(c, q) for c, q in zip(w, [R(1)] + [R(h) for h in hints]) if c != 0]

squares = from_hints(p, HINTS) if HINTS else (from_factors(p) or sos_decomposition(p))
assert squares is not None, 'no sum of squares found; supply candidate squares in HINTS'
proof = linear_combination([(c, sq_nonneg(q, problem)) for c, q in squares if q.degree() > 0], problem)
```

## Worked example

```lean
example (a b : ℚ) : a * b ≤ (a ^ 2 + b ^ 2) / 2 := by
  sage_run file "sos.sage"
-- replacement: linear_combination (1 / 2) * sq_nonneg (a - b)
```

## Failure modes

- **"rounding the SDP solution did not give an exact positive semidefinite Gram matrix":** `p` has real zeros, and every Gram matrix sits on the boundary. Put the squares you expect in `HINTS` (the hinted route is exact).
- **"the polynomial is not a sum of squares":** it may still be nonnegative (the Motzkin polynomial is one). Try `hint_search`, a `case_split` on signs, or multiply by a positive factor first.
- **`linear_combination` fails in Lean:** the goal compared against something other than 0. Restate it as `0 ≤ rhs - lhs`, or use `farkas`/`hint_search`.
