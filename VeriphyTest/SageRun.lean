/-
`sage_run` tests: scripts build proofs with the toolkit; Lean checks them.
Needs a local Sage with `veriphy` installed (`sage -pip install -e .`).
-/
import Mathlib.Basic.Real.Basic
import Mathlib.LinearAlgebra.Matrix.Notation
import Mathlib.Analysis.SpecialFunctions.Sqrt
import Mathlib.Analysis.SpecialFunctions.Complex.Log
import Mathlib.Analysis.SpecialFunctions.Trigonometric.Basic
import Mathlib.LinearAlgebra.Matrix.Determinant.Basic
import Mathlib.LinearAlgebra.Matrix.Trace
import Veriphy

set_option veriphy.checkReplay true

/-! ## Proof shapes -/

-- hint: Sage chooses the square that makes `nlinarith` succeed
example (a b : ℝ) : 0 ≤ a ^ 2 * b ^ 2 - 2 * a * b + 1 := by
  sage_run "proof = nlinarith([sq_nonneg(x0*x1 - 1, problem)])"

-- calc derivation: every step checked on its own
example (x : ℚ) : (x + 1) ^ 2 - 1 = x * (x + 2) := by
  sage_run "proof = calc_chain(term('(x + 1) ^ 2 - 1'), [('=', x0^2 + 2*x0, tactic('ring')), ('=', term('x * (x + 2)'), tactic('ring'))], problem)"

-- case split
example (x : ℚ) : 0 ≤ x * x := by
  sage_run "proof = by_cases('hx', term('0 ≤ x'), tactic('exact mul_nonneg hx hx'), nlinarith())"

-- witness from Sage's kernel computation, side goals by norm_num
example : ∃ v₁ v₂ : ℚ, 2 * v₁ + v₂ = 3 * v₁ ∧ v₁ + 2 * v₂ = 3 * v₂ ∧ v₁ ≠ 0 := by
  sage_run "
M = matrix(QQ, [[-1, 1], [1, -1]])
proof = witness(list(M.right_kernel().basis()[0]), norm_num())"

-- matrix identity (an anticommutator), checked in Sage first, proved entrywise in Lean
example : !![(0 : ℚ), 1; 1, 0] * !![1, 0; 0, -1] + !![1, 0; 0, -1] * !![(0 : ℚ), 1; 1, 0] = 0 := by
  sage_run "
A = matrix(QQ, [[0, 1], [1, 0]]); B = matrix(QQ, [[1, 0], [0, -1]])
assert A*B + B*A == 0
proof = tactic('ext i j\\nfin_cases i <;> fin_cases j <;> simp')"

-- a rewrite step leaves the residual goal for the next tactic
example (x y : ℚ) (h : (x - 1) * (x + 1) = y) : x ^ 2 - 1 = y := by
  sage_run "proof = rewrite_by(x0^2 - 1, term('(x - 1) * (x + 1)'), tactic('ring1'), problem)"
  exact h

-- a saved script from the project, here the Farkas refutation of a linear system
example (x y : ℚ) (h1 : x + y ≤ 1) (h2 : x - y = 3) (h3 : 0 ≤ y) : False := by
  sage_run file "prompts/recipes/templates/farkas.sage"

/-! ## Failures carry the script output, the Lean text and the error -/

/--
error: sage_run: the script's proof does not parse: <sage_run>:1:23: unexpected end of input; expected ')'
── Lean text ──
linear_combination (h
-/
#guard_msgs in
example (x : ℚ) (h : x = 1) : x = 1 := by
  sage_run "proof = 'linear_combination (h'"

-- a wrong hint: nlinarith's failure comes back with the block
example (a b : ℝ) : a * b ≤ (a ^ 2 + b ^ 2) / 2 := by
  fail_if_success sage_run "print('trying a square'); proof = nlinarith([sq_nonneg(x0 + x1, problem)])"
  nlinarith [sq_nonneg (a - b)]

/--
error: sage daemon error: run: ZeroDivisionError: rational division by zero
--- script stdout ---
step 1
-/
#guard_msgs in
example (x : ℚ) (h : x = 1) : x = 1 := by
  sage_run "print('step 1'); 1/0"

/--
error: sage_run: the script's proof does not close the goal:
veriphy: the proof uses `sorry` (sorryAx); only fully checked proofs are accepted
── Lean text ──
sorry
-/
#guard_msgs in
example (x : ℚ) : x = x := by
  sage_run "proof = 'sorry'"

#guard_msgs (drop error) in
example (x : ℚ) : x = x := by
  sage_run file "certificates/missing.sage"

/-! ## Recipe templates on their worked examples -/

example (a b : ℝ) : 0 ≤ a ^ 2 * b ^ 2 - 2 * a * b + 1 := by
  sage_run file "prompts/recipes/templates/hint_search.sage"

example (x : ℚ) : (x + 1) ^ 2 - 1 = x * (x + 2) := by
  sage_run file "prompts/recipes/templates/calc_derivation.sage"

example (x : ℚ) : 0 ≤ x * x := by
  sage_run file "prompts/recipes/templates/case_split.sage"

example : !![(0 : ℚ), 1; 1, 0] * !![1, 0; 0, -1] + !![1, 0; 0, -1] * !![(0 : ℚ), 1; 1, 0] = 0 := by
  sage_run file "prompts/recipes/templates/matrix_identity.sage"

/-! ## Recipe regressions -/

-- farkas: more equalities than unknowns (the equality multipliers are free, so they are not minimized)
example (x y : ℚ) (h1 : x + y = 1) (h2 : x - y = 0) (h3 : 2 * x = 3) : False := by
  sage_run file "prompts/recipes/templates/farkas.sage"

/-! ## Symbolic recipes -/

-- rational_inequality
example (x : ℝ) : x / (x ^ 2 + 1) ≤ 1 / 2 := by
  sage_run file "prompts/recipes/templates/rational_inequality.sage"

-- transcendental_rewrite
example (a b : ℝ) : Real.exp a * Real.exp b = Real.exp (a + b) := by
  sage_run file "prompts/recipes/templates/transcendental_rewrite.sage"
example (x : ℝ) : Real.sin x ^ 2 + Real.cos x ^ 2 = 1 := by
  sage_run file "prompts/recipes/templates/transcendental_rewrite.sage"
-- a pattern entry: the tables bind `log_mul`'s arguments and its side conditions come from the hypotheses
example (x y : ℝ) (hx : x ≠ 0) (hy : y ≠ 0) : Real.log (x * y) = Real.log x + Real.log y := by
  sage_run file "prompts/recipes/templates/transcendental_rewrite.sage"
example (x : ℝ) : Real.cosh x ^ 2 = Real.sinh x ^ 2 + 1 := by
  sage_run file "prompts/recipes/templates/transcendental_rewrite.sage"

-- matrix_from_goal
example : !![(2 : ℚ), 1; 1, 1] * !![1, -1; -1, 2] = 1 := by
  sage_run file "prompts/recipes/templates/matrix_from_goal.sage"
example : !![(0 : ℚ), 1; 1, 0] * !![1, 0; 0, -1] + !![1, 0; 0, -1] * !![0, 1; 1, 0] = 0 := by
  sage_run file "prompts/recipes/templates/matrix_from_goal.sage"
example (c : ℚ) : Matrix.det !![(1 : ℚ), c; 0, 1] = 1 := by
  sage_run file "prompts/recipes/templates/matrix_from_goal.sage"

/-! ## Symbolic translation round trips

Each hypothesis `h : E = 0` is translated to Sage, rendered back to Lean by `symbolic`, and the rendering is proved
equal to `E`. -/

-- rational function and powers
example (x y : ℝ) (h : x / (x ^ 2 + 1) - 1 / y ^ 3 + x ^ 5 = 0) : True := by
  sage_run file "round_trip.sage"
-- the real table: sqrt, exp, log, sin, cos, tan
example (x : ℝ) (h : Real.sqrt x + Real.exp x * Real.log x - Real.sin x / Real.cos x + Real.tan x = 0) : True := by
  sage_run file "round_trip.sage"
-- abs over ℝ and ℤ
example (x : ℝ) (h : |x - 1| - 2 * |x| = 0) : True := by
  sage_run file "round_trip.sage"
example (k : ℤ) (h : |k - 1| + k ^ 2 = 0) : True := by
  sage_run file "round_trip.sage"
-- pi, casts from ℕ and ℤ, natural exponents
example (x : ℝ) (n : ℕ) (k : ℤ) (h : Real.pi * x ^ n - (n : ℝ) / 2 + (k : ℝ) = 0) : True := by
  sage_run file "round_trip.sage"
-- the complex table and I
example (z : ℂ) (h : Complex.exp (z * Complex.I) - Complex.log z + Complex.I * Complex.sin z = 0) : True := by
  sage_run file "round_trip.sage"
