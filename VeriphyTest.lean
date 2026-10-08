/-
Tactic tests. Building this file requires a local Sage (it exercises the live
daemon), so it is not a default target: `lake build VeriphyTest`.
The `Try this:` replacements these produce check WITHOUT Sage — that is the
design rule for committed proofs.
-/
import Mathlib.Data.Real.Basic
import Veriphy

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
