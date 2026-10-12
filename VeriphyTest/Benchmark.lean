/-
The benchmark: every problem the removed certificate tactics solved, now solved by
running a recipe template with `sage_run` (replay on). Needs Sage with `veriphy`.
-/
import Mathlib.Basic.Real.Basic
import Mathlib.Algebra.BigOperators.Group.Finset.Basic
import Veriphy

set_option veriphy.checkReplay true

/-! ## Factorization rewrite (was `sage_factor`) -/

example (x : ℚ) : x ^ 4 - 1 = (x - 1) * (x + 1) * (x ^ 2 + 1) := by
  sage_run file "prompts/recipes/templates/factor_rewrite.sage"
  ring

example (l m x : ℝ) :
    4 * l ^ 2 * x ^ 2 - 4 * l * m ^ 2 * x + m ^ 4 = (2 * l * x - m ^ 2) ^ 2 := by
  sage_run file "prompts/recipes/templates/factor_rewrite.sage"
  ring

example (x y : ℚ) : 3 * x ^ 2 * y - 3 * y ^ 3 = 3 * y * (x - y) * (x + y) := by
  sage_run file "prompts/recipes/templates/factor_rewrite.sage"
  ring

example (f : ℚ → ℚ) (a : ℚ) : f a ^ 2 - a ^ 2 = (f a - a) * (f a + a) := by
  sage_run file "prompts/recipes/templates/factor_rewrite.sage"
  ring

example (x : ℚ) : x ^ 2 / 4 - 1 = (x / 2 - 1) * (x / 2 + 1) := by
  sage_run file "prompts/recipes/templates/factor_rewrite.sage"
  ring

/-! ## Sums of squares (was `sage_sos`) -/

example (x : ℝ) : 0 ≤ x ^ 4 - 2 * x ^ 3 + 2 * x ^ 2 - 2 * x + 1 := by
  sage_run file "prompts/recipes/templates/sos.sage"

example (l m x : ℝ) : 4 * l ^ 2 * x ^ 2 - 4 * l * m ^ 2 * x + m ^ 4 ≥ 0 := by
  sage_run file "prompts/recipes/templates/sos.sage"

example (x : ℚ) : 0 ≤ x ^ 2 + x + 1 := by
  sage_run file "prompts/recipes/templates/sos.sage"

example (x y : ℚ) : 0 ≤ 35 / 2 * (x * y - 1) ^ 2 + 0 * x := by
  sage_run file "prompts/recipes/templates/sos.sage"

example (x y : ℚ) : 0 ≤ (35 / 2 : ℚ) * x ^ 2 * y ^ 2 - 35 * x * y + 35 / 2 := by
  sage_run file "prompts/recipes/templates/sos.sage"

example (a b : ℚ) : 0 ≤ a ^ 4 + 2 * a ^ 2 * b ^ 2 + b ^ 4 - 2 * a ^ 2 - 2 * b ^ 2 + 1 + (a - b) ^ 2 := by
  sage_run file "VeriphyTest/certificates/sos_hinted_quartic.sage"

example (a b : ℚ) : a * b ≤ (a ^ 2 + b ^ 2) / 2 := by
  sage_run file "prompts/recipes/templates/sos.sage"

/-! ## Ideal membership (was `sage_lincomb`, `sage_certify identity`) -/

example (x y : ℚ) (h1 : x - y = 0) (h2 : x + y - 2 = 0) : x ^ 2 - y ^ 2 = 0 := by
  sage_run file "prompts/recipes/templates/ideal_membership.sage"

example (a b : ℝ) (h : a + b = 3) (h' : a * b = 2) : a ^ 2 + b ^ 2 = 5 := by
  sage_run file "prompts/recipes/templates/ideal_membership.sage"

example (v₁ v₂ v₃ : ℚ) (h1 : v₁ + v₂ = 0) (h2 : v₂ + v₃ = 0) : v₁ = v₃ := by
  sage_run file "prompts/recipes/templates/ideal_membership.sage"

-- an inaccessible hypothesis is never offered to the script
example (x y : ℚ) (h : x = y) : x = y → x + 1 = y + 1 := by
  intro
  sage_run file "prompts/recipes/templates/ideal_membership.sage"

example (a b : ℝ) (h : a + b = 3) (h' : a * b = 2) : a ^ 2 + b ^ 2 = 5 := by
  sage_run file "prompts/recipes/templates/ideal_membership.sage"

/-! ## Witnesses (was `sage_witness`, `sage_exists`, `sage_certify witness`) -/

example : ∃ x : ℚ, 2 * x ^ 3 - 3 * x ^ 2 - 3 * x + 2 = 0 := by
  sage_run file "prompts/recipes/templates/witness.sage"

example : ∃ x : ℚ, x ^ 2 - x - 6 = 0 := by
  sage_run file "prompts/recipes/templates/witness.sage"

example : ∃ v₁ v₂ : ℚ, 2 * v₁ + v₂ = 3 * v₁ ∧ v₁ + 2 * v₂ = 3 * v₂ ∧ v₁ ≠ 0 := by
  sage_run file "prompts/recipes/templates/witness.sage"

example : ∃ x y : ℚ, x + y = 1 ∧ 0 < x ∧ x < y := by
  sage_run file "prompts/recipes/templates/witness.sage"

-- no inequalities: no LP is built
example : ∃ x y : ℚ, x = y := by
  sage_run file "prompts/recipes/templates/witness.sage"

example : ∃ v₁ v₂ : ℚ, 2 * v₁ + v₂ = 3 * v₁ ∧ v₁ + 2 * v₂ = 3 * v₂ ∧ v₁ ≠ 0 := by
  sage_run file "prompts/recipes/templates/witness.sage"

/-! ## Sums by induction (was `sage_sum`) -/

example (n : ℕ) :
    ∑ k ∈ Finset.range n, (k : ℚ) ^ 2 = (n : ℚ) ^ 3 / 3 - (n : ℚ) ^ 2 / 2 + (n : ℚ) / 6 := by
  sage_run file "prompts/recipes/templates/sum_induction.sage"

example (n : ℕ) :
    ∑ k ∈ Finset.range n, ((k : ℚ) ^ 3 + 1) = ((n : ℚ) ^ 2 * ((n : ℚ) - 1) ^ 2) / 4 + n := by
  sage_run file "prompts/recipes/templates/sum_induction.sage"

/-! ## Farkas refutation (was `sage_farkas`, `sage_certify inequality`) -/

example (x y : ℚ) (h1 : x + y ≤ 1) (h2 : x - y = 3) (h3 : 0 ≤ y) : False := by
  sage_run file "prompts/recipes/templates/farkas.sage"

-- an anomaly-style system: nonnegative multiplicities and linear cancellation conditions
example (a b c : ℚ) (ha : 0 ≤ a) (hb : 0 ≤ b) (hc : 0 ≤ c)
    (e1 : 2 * a + b - c = 0) (e2 : a + 3 * c = 0) : a + b + c ≤ 0 := by
  sage_run file "prompts/recipes/templates/farkas.sage"

example (p q : ℚ) (h1 : p < q) (h2 : q ≤ p) : False := by
  sage_run file "prompts/recipes/templates/farkas.sage"

-- the negation step introduces a fresh, printable hypothesis
example (u v : ℚ) (h1 : 0 ≤ u) (h2 : u + v = 0) (h3 : 0 ≤ v) : u ≤ 0 := by
  sage_run file "prompts/recipes/templates/farkas.sage"

-- only equality hypotheses: the LP has no inequality rows
example (x : ℚ) (h1 : x = 1) (h2 : x = 2) : False := by
  sage_run file "prompts/recipes/templates/farkas.sage"

-- a `≥` goal is negated too
example (a b : ℚ) (h1 : a - b = 2) : a ≥ b := by
  sage_run file "prompts/recipes/templates/farkas.sage"

example (x y : ℚ) (h1 : x + y ≤ 1) (h2 : x - y = 3) (h3 : 0 ≤ y) : False := by
  sage_run file "prompts/recipes/templates/farkas.sage"
