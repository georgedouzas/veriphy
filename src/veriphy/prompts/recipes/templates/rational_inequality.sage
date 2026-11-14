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
