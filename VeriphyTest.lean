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
