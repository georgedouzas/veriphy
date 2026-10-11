/-
Tactic tests. Building this file requires a local Sage (it exercises the live
daemon), so it is not a default target: `lake build VeriphyTest`.
The `Try this:` replacements these produce check WITHOUT Sage — that is the
design rule for committed proofs.
-/
import Mathlib.Data.Real.Basic
import Veriphy

-- every emitted replacement is re-parsed and re-run with Sage disabled
set_option veriphy.checkReplay true

-- Classic: the tactic rewrites the goal to its certified factored form.
example (x : ℚ) : x ^ 4 - 1 = (x - 1) * (x + 1) * (x ^ 2 + 1) := by
  sage_factor
  ring

-- The Higgs-potential discriminant is a perfect square (over ℝ).
example (l m x : ℝ) :
    4 * l ^ 2 * x ^ 2 - 4 * l * m ^ 2 * x + m ^ 4 = (2 * l * x - m ^ 2) ^ 2 := by
  sage_factor
  ring

-- Multivariate, with a nontrivial unit (content 3) pulled out by Sage.
example (x y : ℚ) : 3 * x ^ 2 * y - 3 * y ^ 3 = 3 * y * (x - y) * (x + y) := by
  sage_factor
  ring

-- Atoms need not be variables: compound subterms become indeterminates.
example (f : ℚ → ℚ) (a : ℚ) :
    f a ^ 2 - a ^ 2 = (f a - a) * (f a + a) := by
  sage_factor
  ring

/-! ## sage_sos -/

-- Sage finds x⁴-2x³+2x²-2x+1 = (x²-x)² + (x-1)²; positivity + ring1 certify.
example (x : ℝ) : 0 ≤ x ^ 4 - 2 * x ^ 3 + 2 * x ^ 2 - 2 * x + 1 := by
  sage_sos

-- The Higgs discriminant again, now as the inequality it exists to prove.
example (l m x : ℝ) : 4 * l ^ 2 * x ^ 2 - 4 * l * m ^ 2 * x + m ^ 4 ≥ 0 := by
  sage_sos

-- Positive-definite quadratic: completing the square, exact over ℚ.
example (x : ℚ) : 0 ≤ x ^ 2 + x + 1 := by
  sage_sos

/-! ## sage_lincomb (local polyrith) -/

example (x y : ℚ) (h1 : x - y = 0) (h2 : x + y - 2 = 0) :
    x ^ 2 - y ^ 2 = 0 := by
  sage_lincomb

example (a b : ℝ) (h : a + b = 3) (h' : a * b = 2) :
    a ^ 2 + b ^ 2 = 5 := by
  sage_lincomb

/-! ## sage_witness -/

-- Sage finds the rational root 2 (or 1/2 or -1); norm_num checks it.
example : ∃ x : ℚ, 2 * x ^ 3 - 3 * x ^ 2 - 3 * x + 2 = 0 := by
  sage_witness

example : ∃ x : ℚ, x ^ 2 - x - 6 = 0 := by
  sage_witness

/-! ## sage_sum (discovery: #sage_sum; proof: kernel-only induction) -/

#sage_sum "k^2"

example (n : ℕ) :
    ∑ k ∈ Finset.range n, (k : ℚ) ^ 2
      = (n : ℚ) ^ 3 / 3 - (n : ℚ) ^ 2 / 2 + (n : ℚ) / 6 := by
  sage_sum n

example (n : ℕ) :
    ∑ k ∈ Finset.range n, ((k : ℚ) ^ 3 + 1)
      = ((n : ℚ) ^ 2 * ((n : ℚ) - 1) ^ 2) / 4 + n := by
  sage_sum n

/-! ## Rational coefficients (division by numerals is read as a coefficient) -/

example (x y : ℚ) : 0 ≤ 35 / 2 * (x * y - 1) ^ 2 + 0 * x := by
  sage_sos

example (x y : ℚ) : 0 ≤ (35 / 2 : ℚ) * x ^ 2 * y ^ 2 - 35 * x * y + 35 / 2 := by
  sage_sos

example (x : ℚ) : x ^ 2 / 4 - 1 = (x / 2 - 1) * (x / 2 + 1) := by
  sage_factor
  ring

/-! ## sage_sos with hinted squares -/

-- Irreducible quartic; the squares are supplied, Sage finds the nonnegative weights.
example (a b : ℚ) : 0 ≤ a ^ 4 + 2 * a ^ 2 * b ^ 2 + b ^ 4 - 2 * a ^ 2 - 2 * b ^ 2 + 1 + (a - b) ^ 2 := by
  sage_sos [a ^ 2 + b ^ 2 - 1, a - b]

/-! ## sage_farkas (linear arithmetic by an exact Farkas certificate) -/

example (x y : ℚ) (h1 : x + y ≤ 1) (h2 : x - y = 3) (h3 : 0 ≤ y) : False := by
  sage_farkas

-- an anomaly-style system: nonnegative multiplicities and linear cancellation conditions
example (a b c : ℚ) (ha : 0 ≤ a) (hb : 0 ≤ b) (hc : 0 ≤ c)
    (e1 : 2 * a + b - c = 0) (e2 : a + 3 * c = 0) : a + b + c ≤ 0 := by
  sage_farkas

example (p q : ℚ) (h1 : p < q) (h2 : q ≤ p) : False := by
  sage_farkas

/-! ## sage_exists (rational witnesses) -/

-- generalized eigenvector: V v = λ K v with V = [[2,1],[1,2]], K = I, λ = 3, v ≠ 0
example : ∃ v₁ v₂ : ℚ, 2 * v₁ + v₂ = 3 * v₁ ∧ v₁ + 2 * v₂ = 3 * v₂ ∧ v₁ ≠ 0 := by
  sage_exists

example : ∃ x y : ℚ, x + y = 1 ∧ 0 < x ∧ x < y := by
  sage_exists

/-! ## kernel spans via sage_lincomb: the kernel of [[1,1,0],[0,1,1]] is spanned by (1,-1,1) -/

example (v₁ v₂ v₃ : ℚ) (h1 : v₁ + v₂ = 0) (h2 : v₂ + v₃ = 0) : v₁ = v₃ := by
  sage_lincomb

-- the emitted replacement must re-parse: a goal that needs the negation step
example (u v : ℚ) (h1 : 0 ≤ u) (h2 : u + v = 0) (h3 : 0 ≤ v) : u ≤ 0 := by
  sage_farkas

/-! ## Regressions (replay on) -/

-- an inaccessible hypothesis is never collected (it could not be printed)
example (x y : ℚ) (h : x = y) : x = y → x + 1 = y + 1 := by
  intro
  sage_lincomb

-- only equality hypotheses: the LP has no inequality rows (empty-LP guard)
example (x : ℚ) (h1 : x = 1) (h2 : x = 2) : False := by
  sage_farkas

-- a `≥` goal is negated too
example (a b : ℚ) (h1 : a - b = 2) : a ≥ b := by
  sage_farkas

-- no inequalities: no LP is built
example : ∃ x y : ℚ, x = y := by
  sage_exists

/-! ## sage_certify (agent-written certificates; the emitted proof is the plain checker proof) -/

-- identity: the script computes the ideal-membership cofactors itself
example (a b : ℝ) (h : a + b = 3) (h' : a * b = 2) : a ^ 2 + b ^ 2 = 5 := by
  sage_certify identity "
cs = goal.poly.lift(R.ideal([h.poly for h in hyps]))
certificate = {'cofactors': {h.name: c for h, c in zip(hyps, cs)}}"

-- inequality: a weighted square, with a constant slack absorbed by the checker
example (a b : ℚ) : a * b ≤ (a ^ 2 + b ^ 2) / 2 := by
  sage_certify inequality "certificate = {'squares': [(1/2, x0 - x1)]}"

-- inequality refuting `False`: Farkas weights; the daemon reports κ = 2
example (x y : ℚ) (h1 : x + y ≤ 1) (h2 : x - y = 3) (h3 : 0 ≤ y) : False := by
  sage_certify inequality "certificate = {'h1': 1, 'h2': -1, 'h3': 2}"

-- witness: an eigenvector from Sage's kernel computation
example : ∃ v₁ v₂ : ℚ, 2 * v₁ + v₂ = 3 * v₁ ∧ v₁ + 2 * v₂ = 3 * v₂ ∧ v₁ ≠ 0 := by
  sage_certify witness "
M = matrix(QQ, [[-1, 1], [1, -1]])
certificate = list(M.right_kernel().basis()[0])"

-- family/goal mismatch: rejected by extraction, before Sage is contacted
/--
error: sage_certify witness: goal must be `∃ …`, got
  x ≤ y
-/
#guard_msgs in
example (x y : ℚ) (h : x ≤ y) : x ≤ y := by
  sage_certify witness "certificate = []"

-- weights that do not imply the goal: the checker rejects them
example (a b : ℚ) : a * b ≤ (a ^ 2 + b ^ 2) / 2 := by
  fail_if_success sage_certify inequality "certificate = {'squares': [(1/4, x0 - x1)]}"
  linear_combination (1 / 2) * sq_nonneg (a - b)

-- a witness of the wrong arity: rejected with the family named
example : ∃ x y : ℚ, x + y = 1 := by
  fail_if_success sage_certify witness "certificate = [1]"
  exact ⟨1, 0, by norm_num⟩
