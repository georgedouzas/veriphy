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
import Mathlib.Analysis.SpecialFunctions.Trigonometric.Inverse
import Mathlib.Analysis.SpecialFunctions.Trigonometric.Arctan
import Mathlib.Analysis.SpecialFunctions.Log.Base
import Mathlib.Analysis.SpecialFunctions.Pow.Real
import Mathlib.Algebra.Order.Floor.Ring
import Mathlib.Data.Nat.Choose.Basic
import Mathlib.Analysis.SpecialFunctions.Gamma.Basic
import Mathlib.Analysis.SpecialFunctions.Arsinh
import Veriphy
import VeriphyCheck

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

-- sums over intervals
example (n : ℕ) : ∑ k ∈ Finset.Icc 1 n, (k : ℚ) = n * (n + 1) / 2 := by
  sage_run file "prompts/recipes/templates/sum_induction.sage"
example (n : ℕ) : ∑ k ∈ Finset.Ico 1 n, (2 * k : ℚ) = n * (n - 1) := by
  sage_run file "prompts/recipes/templates/sum_induction.sage"
example (n : ℕ) : ∑ k ∈ Finset.Ico 0 n, (k : ℚ) ^ 3 = (n * (n - 1) / 2) ^ 2 := by
  sage_run file "prompts/recipes/templates/sum_induction.sage"

-- ODEs: a stated solution, and solutions Sage finds
example (ω A B : ℝ) (x : ℝ → ℝ) (hx : x = fun s => A * Real.cos (ω * s) + B * Real.sin (ω * s)) (t : ℝ) :
    deriv (deriv x) t + ω ^ 2 * x t = 0 := by
  sage_run "proof = verify_definition(problem)"
example : ∃ x : ℝ → ℝ, (∀ t, deriv x t = 2 * x t) ∧ x 0 = 3 := by
  sage_run file "prompts/recipes/templates/ode_solution.sage"
example (ω x₀ v₀ : ℝ) (hω : ω ≠ 0) :
    ∃ x : ℝ → ℝ, (∀ t, deriv (deriv x) t + ω ^ 2 * x t = 0) ∧ x 0 = x₀ ∧ deriv x 0 = v₀ := by
  sage_run file "prompts/recipes/templates/ode_solution.sage"
-- a wrong solution fails with the residual Lean could not close
/--
error: sage_run: the script's proof does not close the goal:
veriphy: the certificate check failed:
unsolved goals
d1 : (deriv fun s => 3 * Real.exp (3 * s)) = fun s => 9 * Real.exp (3 * s)
t : ℝ
⊢ Real.exp (t * 3) * 9 = Real.exp (t * 3) * 6
── Lean text ──
have d1 : deriv (fun s => 3 * (Real.exp (3 * s))) = fun s => 9 * (Real.exp (3 * s)) := by
  funext s
  have hd : HasDerivAt (fun s => 3 * (Real.exp (3 * s))) ((9 * (Real.exp (3 * s)) : ℝ)) (s) := by
    convert ((((hasDerivAt_id' (s : ℝ)).const_mul (3 : ℝ)).exp).const_mul (3 : ℝ)) using 1
    all_goals first | rfl | (funext y; ring_nf; done) | (first | ring1 | (ring_nf; done) | (field_simp; done) | (field_simp; ring1) | (field_simp; ring_nf; done) | (norm_num; done))
  exact hd.deriv
exact ⟨fun s => 3 * (Real.exp (3 * s)), fun t => by (simp only [d1]; first | ring1 | (ring_nf; done) | (field_simp; done) | (field_simp; ring1) | (field_simp; ring_nf; done) | (norm_num; done) | ring_nf)⟩
-/
#guard_msgs in
example : ∃ x : ℝ → ℝ, ∀ t, deriv x t = 2 * x t := by
  sage_run "proof = solve_exists(problem, solution=3 * exp(3 * SR.var('s_')))"

-- derivative
example : deriv (fun x : ℝ => x ^ 2 * Real.exp x) 1 = 3 * Real.exp 1 := by
  sage_run file "prompts/recipes/templates/derivative.sage"
example (a : ℝ) (ha : a ≠ 0) : deriv (fun x : ℝ => Real.log x * Real.sin x) a =
    Real.sin a / a + Real.log a * Real.cos a := by
  sage_run file "prompts/recipes/templates/derivative.sage"

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

-- hyperbolic and inverse trigonometric functions, real powers
example (x y : ℝ) (h : Real.cosh x - Real.sinh x * Real.tanh x + Real.arctan x - x ^ y = 0) : True := by
  sage_run file "round_trip.sage"
example (x : ℝ) (h : Real.arcsin x + 2 * Real.arccos x = 0) : True := by
  sage_run file "round_trip.sage"
-- factorial, choose, gcd, floor and ceil, rendered at their own type and cast
example (x : ℝ) (m n k : ℕ) (h : (Nat.factorial n : ℝ) * x + Nat.choose n k - Nat.gcd m n = 0) : True := by
  sage_run file "round_trip.sage"
example (x : ℝ) (h : (⌊x⌋ : ℝ) + ⌈x⌉ - x = 0) : True := by
  sage_run file "round_trip.sage"
-- a natural-number remainder inside a real expression keeps its cast
example (x : ℝ) (n : ℕ) (h : ((n % 7 : ℕ) : ℝ) + x = 0) : True := by
  sage_run file "round_trip.sage"
-- `logb` becomes `log x / log b` in Sage; unfolding `Real.logb` relates the two
example (b x : ℝ) (h : Real.logb b x - 1 = 0) : True := by
  sage_run "
h = hyps[0]
proof = steps(tactic(f'have _r : {symbolic(h.expr, problem)} = 0 := by\\n  simp only [Real.logb] at {h.name}\\n  linear_combination {h.name}'), tactic('trivial'))"

/-! ## Checking project translation entries -/

/--
error: passed: Real.Gamma ↔ gamma
passed: rw [Real.Gamma_add_one]
failed: Real.arsinh ↔ asinhh: sage daemon error: run: AssertionError: Sage could not read the translation: check the sage name
-/
#guard_msgs in
#veriphy_check_translations "VeriphyTest/fixtures/check"

/-! ## Reflective certificates -/

-- small matrices get the readable entrywise proof
example : !![(1 : ℤ), 2; 3, 4] * !![0, 1; 1, 0] = !![2, 1; 4, 3] := by
  sage_run "proof = matrix_goal_proof('mul', 2, 'ℤ')"

-- a 16×16 commutation is checked by the kernel through VeriphyCheck
set_option maxRecDepth 100000 in
example : (!![0, -2, 0, 0, 0, 0, 0, 0, 0, -1, 0, -1, 1, 0, 0, 0; -2, 0, 0, 0, -2, 0, -1, -1, 0, 0, 0, 0, 0, 0, 0, 0; 0, 0, 0, 0, 0, 0, 2, 0, 0, 0, 0, -1, 0, 0, -2, 0; 0, 0, 0, 0, 0, 0, 0, 2, 0, 2, 0, 0, 0, 1, 0, 0; 0, 0, 0, 0, 0, 0, 0, 0, 2, 1, -2, 0, 0, 0, 0, 0; 0, 0, 0, 0, 0, 0, -1, 0, 0, 0, 0, -2, 0, 2, -1, 0; 0, 0, 0, 0, 0, 0, 0, -1, 0, 0, -2, 0, 2, 0, -2, 0; 0, 1, 0, 0, 0, 0, 0, 1, -1, 0, 0, 0, 0, 0, 0, 0; 0, -2, 2, 0, 0, -2, 0, 0, -2, 0, 0, 0, 0, 0, 0, 0; 0, 0, 0, 0, 2, 0, 1, 0, 0, 0, 0, 0, -1, 0, 0, -2; 0, 0, 0, -2, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, -1; 0, 0, -2, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, -1, 0, 0; 0, 0, -1, 0, 0, 1, 2, 1, 0, 0, 0, 0, 0, 0, 0, 0; 0, 0, 0, 0, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, -1, -1; -1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 2, 0, 0, 0, -2, 0; 0, 0, 0, 1, 1, 0, 1, 0, 0, 0, -1, 0, 0, 0, 0, 0] : Matrix (Fin 16) (Fin 16) ℤ) * !![4, 2, 1, 0, 2, 1, 3, 3, 0, 1, -1, 1, 0, 1, 0, 2; 2, 3, 0, 0, 2, 0, 1, 1, -3, 0, 6, 2, -4, 0, 2, 0; 2, 0, 2, -2, 0, 0, -2, -2, 0, 0, -9, 1, 4, 1, 2, 0; 0, 2, 0, 0, 4, 0, 2, 0, 0, -2, 0, 0, -2, -1, -1, -5; 0, -4, 4, 4, 2, -4, 1, -2, -6, -1, 2, 0, -1, -2, 0, 0; 1, 0, 4, -1, 0, 0, 1, 1, 4, 0, -2, 2, -2, 0, 3, -2; 2, -1, -2, 2, 0, 2, 4, 0, 1, 0, -2, 0, -2, -2, 6, 2; -2, 2, -2, 0, -2, 2, -1, -1, 2, 0, 0, 0, 0, 0, 0, 0; 4, 6, -6, 0, 4, 6, 8, 2, 6, 0, 0, 2, 0, -4, -2, 0; 0, 0, 1, -2, -4, -1, -5, -2, 4, 2, -4, 0, 3, 0, -2, 2; 0, 1, 0, 1, -1, 0, -1, -4, 1, -4, 1, 0, 0, -3, -1, 0; 0, 0, 2, -2, 0, 0, -4, 1, -2, 0, -1, 2, 0, 2, 5, 0; 0, 1, 1, 0, 0, -1, -5, -2, -1, 0, -4, -1, 4, 2, -3, 0; 1, -4, 4, -2, -1, -4, -1, 0, -6, 0, -1, 0, 0, 0, 3, 1; 3, 2, 0, -7, 0, 0, 0, 4, 0, 3, -6, 1, -1, 3, 6, -2; 0, 0, 0, 1, -1, 0, -1, 0, 2, 3, -3, 0, 2, 0, -2, 1] = !![4, 2, 1, 0, 2, 1, 3, 3, 0, 1, -1, 1, 0, 1, 0, 2; 2, 3, 0, 0, 2, 0, 1, 1, -3, 0, 6, 2, -4, 0, 2, 0; 2, 0, 2, -2, 0, 0, -2, -2, 0, 0, -9, 1, 4, 1, 2, 0; 0, 2, 0, 0, 4, 0, 2, 0, 0, -2, 0, 0, -2, -1, -1, -5; 0, -4, 4, 4, 2, -4, 1, -2, -6, -1, 2, 0, -1, -2, 0, 0; 1, 0, 4, -1, 0, 0, 1, 1, 4, 0, -2, 2, -2, 0, 3, -2; 2, -1, -2, 2, 0, 2, 4, 0, 1, 0, -2, 0, -2, -2, 6, 2; -2, 2, -2, 0, -2, 2, -1, -1, 2, 0, 0, 0, 0, 0, 0, 0; 4, 6, -6, 0, 4, 6, 8, 2, 6, 0, 0, 2, 0, -4, -2, 0; 0, 0, 1, -2, -4, -1, -5, -2, 4, 2, -4, 0, 3, 0, -2, 2; 0, 1, 0, 1, -1, 0, -1, -4, 1, -4, 1, 0, 0, -3, -1, 0; 0, 0, 2, -2, 0, 0, -4, 1, -2, 0, -1, 2, 0, 2, 5, 0; 0, 1, 1, 0, 0, -1, -5, -2, -1, 0, -4, -1, 4, 2, -3, 0; 1, -4, 4, -2, -1, -4, -1, 0, -6, 0, -1, 0, 0, 0, 3, 1; 3, 2, 0, -7, 0, 0, 0, 4, 0, 3, -6, 1, -1, 3, 6, -2; 0, 0, 0, 1, -1, 0, -1, 0, 2, 3, -3, 0, 2, 0, -2, 1] * !![0, -2, 0, 0, 0, 0, 0, 0, 0, -1, 0, -1, 1, 0, 0, 0; -2, 0, 0, 0, -2, 0, -1, -1, 0, 0, 0, 0, 0, 0, 0, 0; 0, 0, 0, 0, 0, 0, 2, 0, 0, 0, 0, -1, 0, 0, -2, 0; 0, 0, 0, 0, 0, 0, 0, 2, 0, 2, 0, 0, 0, 1, 0, 0; 0, 0, 0, 0, 0, 0, 0, 0, 2, 1, -2, 0, 0, 0, 0, 0; 0, 0, 0, 0, 0, 0, -1, 0, 0, 0, 0, -2, 0, 2, -1, 0; 0, 0, 0, 0, 0, 0, 0, -1, 0, 0, -2, 0, 2, 0, -2, 0; 0, 1, 0, 0, 0, 0, 0, 1, -1, 0, 0, 0, 0, 0, 0, 0; 0, -2, 2, 0, 0, -2, 0, 0, -2, 0, 0, 0, 0, 0, 0, 0; 0, 0, 0, 0, 2, 0, 1, 0, 0, 0, 0, 0, -1, 0, 0, -2; 0, 0, 0, -2, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, -1; 0, 0, -2, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, -1, 0, 0; 0, 0, -1, 0, 0, 1, 2, 1, 0, 0, 0, 0, 0, 0, 0, 0; 0, 0, 0, 0, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, -1, -1; -1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 2, 0, 0, 0, -2, 0; 0, 0, 0, 1, 1, 0, 1, 0, 0, 0, -1, 0, 0, 0, 0, 0] := by
  sage_run "proof = matrix_goal_proof('commute', 16, 'ℤ')"

-- a Pratt certificate
example : Nat.Prime 1000000007 := by
  sage_run "proof = tactic('exact ' + str(prime_certificate(1000000007)))"
