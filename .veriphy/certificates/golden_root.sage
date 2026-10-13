# name: golden_root
# technique: isolated real roots by sign changes and monotonicity; eigenvalues through the characteristic polynomial
# goal: ∃! x : ℝ, (a < x ∧ x < b) ∧ p x = 0, or an eigenvalue of an explicit 3 by 3 matrix in an interval
# description: Sage isolates the roots; Lean applies the intermediate value theorem and strict monotonicity.
x = polygen(QQ, 'x')
POLYNOMIAL = x**3 - 2*x - 1
POLYNOMIAL_LEAN = 'x ^ 3 - 2 * x - 1'
INTERVAL = (QQ(3) / 2, 3)
assert POLYNOMIAL is not None, 'fill in POLYNOMIAL and POLYNOMIAL_LEAN in a copy'
if INTERVAL is None:
    raise AssertionError(f'isolating intervals: {isolate_roots(POLYNOMIAL)}; state the goal on one and set INTERVAL')
proof = root_proof(POLYNOMIAL_LEAN, INTERVAL[0], INTERVAL[1], POLYNOMIAL)
