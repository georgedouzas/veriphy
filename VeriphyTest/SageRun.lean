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
import Mathlib.Analysis.SpecialFunctions.Gamma.Basic
import Mathlib.Analysis.SpecialFunctions.Trigonometric.Arctan
import Mathlib.Analysis.SpecialFunctions.Log.Base
import Mathlib.Analysis.SpecialFunctions.Pow.Real
import Mathlib.Algebra.Order.Floor.Ring
import Mathlib.Data.Nat.Choose.Basic
import Mathlib.Analysis.SpecialFunctions.Gamma.Basic
import Mathlib.Analysis.SpecialFunctions.Arsinh
import Mathlib.Analysis.Normed.Algebra.MatrixExponential
import Mathlib.Analysis.SpecialFunctions.Trigonometric.DerivHyp
import Mathlib.Analysis.Calculus.FDeriv.Symmetric
import Veriphy
import VeriphyCheck
import Mathlib.LinearAlgebra.Matrix.Cartan.Basic
import Mathlib.RingTheory.Polynomial.Cyclotomic.Roots

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
-- a rewrite entry from the project's own tables, picked by the template unedited
set_option veriphy.translationsDir "VeriphyTest/fixtures/project_translations" in
example (x : ℝ) (hx : x ≠ 0) : Real.Gamma (x + 1) = x * Real.Gamma x := by
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

/-! ## Lie algebras of explicit matrices -/

namespace LieTest

def e : Matrix (Fin 2) (Fin 2) ℚ := !![0, 1; 0, 0]
def f : Matrix (Fin 2) (Fin 2) ℚ := !![0, 0; 1, 0]
def h : Matrix (Fin 2) (Fin 2) ℚ := !![1, 0; 0, -1]
def C : Matrix (Fin 2) (Fin 2) ℚ := !![3 / 8, 0; 0, 3 / 8]

-- the bracket table of 𝔰𝔩₂, from Sage's structure constants, each relation checked by the kernel
example : ⁅h, e⁆ = 2 • e ∧ ⁅h, f⁆ = -2 • f ∧ ⁅e, f⁆ = h := by
  sage_run "
basis = [matrix(QQ, [[0, 1], [0, 0]]), matrix(QQ, [[0, 0], [1, 0]]), matrix(QQ, [[1, 0], [0, -1]])]
proof = steps(bracket_relations(basis, ['e', 'f', 'h'], pairs=[(2, 0), (2, 1), (0, 1)]),
              tactic('exact ⟨hb_2_0, hb_2_1, hb_0_1⟩'))"

-- the same relations proved entrywise
example : ⁅h, e⁆ = 2 • e := by
  sage_run "
basis = [matrix(QQ, [[0, 1], [0, 0]]), matrix(QQ, [[0, 0], [1, 0]]), matrix(QQ, [[1, 0], [0, -1]])]
proof = steps(bracket_relations(basis, ['e', 'f', 'h'], pairs=[(2, 0)], entrywise_limit=2), tactic('exact hb_2_0'))"

-- the Casimir (for the Killing form) commutes with the basis
example : C * e = e * C ∧ C * f = f * C ∧ C * h = h * C := by
  sage_run "
basis = [matrix(QQ, [[0, 1], [0, 0]]), matrix(QQ, [[0, 0], [1, 0]]), matrix(QQ, [[1, 0], [0, -1]])]
assert casimir(basis) == matrix(QQ, [[3/8, 0], [0, 3/8]]), casimir(basis)
proof = steps(commutation_facts('C', ['e', 'f', 'h'], size=2), tactic('exact ⟨hc_0, hc_1, hc_2⟩'))"

-- su(3) in a basis with rational structure constants: the Jacobi identity, through the structure-constant checker
set_option maxRecDepth 100000 in
example : True := by
  sage_run "
K = QuadraticField(-1, 'i'); i = K.gen()
def E(a, b):
    m = matrix(K, 3, 3); m[a, b] = 1; return m
basis = [i*(E(0,0)-E(1,1)), i*(E(1,1)-E(2,2)), E(0,1)-E(1,0), E(0,2)-E(2,0), E(1,2)-E(2,1),
         i*(E(0,1)+E(1,0)), i*(E(0,2)+E(2,0)), i*(E(1,2)+E(2,1))]
proof = steps(jacobi_certificate(structure_constants(basis)), tactic('trivial'))"

end LieTest

/-! ## Root data, checked against mathlib's Cartan matrices -/

-- the determinant of E₈ from an LU factorization over ℚ the kernel checks
set_option maxRecDepth 10000 in
example : (CartanMatrix.E 8).det = 1 := by
  sage_run "proof = tactic('exact ' + str(det_certificate(cartan_matrix('E8'))))"

-- the inverse of F₄, from Sage, checked by the product
example : CartanMatrix.F₄⁻¹ = !![2, 3, 4, 2; 3, 6, 8, 4; 2, 4, 6, 3; 1, 2, 3, 2] := by
  sage_run "
assert cartan_matrix('F4').inverse() == matrix(QQ, [[2, 3, 4, 2], [3, 6, 8, 4], [2, 4, 6, 3], [1, 2, 3, 2]])
proof = tactic('exact ' + str(inverse_certificate()))"

-- the toolkit's conventions are mathlib's, type by type
example : CartanMatrix.F₄ = !![2, -1, 0, 0; -1, 2, -2, 0; 0, -1, 2, -1; 0, 0, -1, 2] ∧
    CartanMatrix.G₂ = !![2, -3; -1, 2] ∧ CartanMatrix.B 3 = !![2, -1, 0; -1, 2, -2; 0, -1, 2] ∧
    CartanMatrix.C 3 = !![2, -1, 0; -1, 2, -1; 0, -2, 2] ∧ CartanMatrix.D 4 = !![2, -1, 0, 0; -1, 2, -1, -1; 0, -1, 2, 0; 0, -1, 0, 2] := by
  sage_run "
expected = [cartan_matrix(t) for t in ['F4', 'G2', 'B3', 'C3', 'D4']]
assert [[list(r) for r in m.rows()] for m in expected] == [
    [[2, -1, 0, 0], [-1, 2, -2, 0], [0, -1, 2, -1], [0, 0, -1, 2]], [[2, -3], [-1, 2]],
    [[2, -1, 0], [-1, 2, -2], [0, -1, 2]], [[2, -1, 0], [-1, 2, -1], [0, -2, 2]],
    [[2, -1, 0, 0], [-1, 2, -1, -1], [0, -1, 2, 0], [0, -1, 0, 2]]], expected
proof = tactic('exact ⟨by decide, by decide, by decide, by decide, by decide⟩')"

/-! ## The `lie_structure` recipe -/

-- a bracket of explicit matrices, with the template unedited
example : ⁅!![(0 : ℚ), 1; 0, 0], !![(0 : ℚ), 0; 1, 0]⁆ = !![(1 : ℚ), 0; 0, -1] := by
  sage_run file "prompts/recipes/templates/lie_structure.sage"

-- the bracket table of 𝔰𝔩₂ by name, from a copy of the template with BASIS and NAMES filled in
example : ⁅LieTest.h, LieTest.e⁆ = 2 • LieTest.e ∧ ⁅LieTest.e, LieTest.f⁆ = LieTest.h := by
  sage_run file "lie_sl2.sage"

-- the determinant of E₈, from a copy with CARTAN filled in
set_option maxRecDepth 10000 in
example : (CartanMatrix.E 8).det = 1 := by
  sage_run file "cartan_e8.sage"

/-! ## Exact number fields -/

-- ℚ(√2): a scalar identity, by reducing powers of `Real.sqrt 2` with `Real.sqrt 2 ^ 2 = 2`
example : (1 + Real.sqrt 2) ^ 3 = 7 + 5 * Real.sqrt 2 := by
  sage_run "
K = QuadraticField(2, 's'); s = K.gen()
assert (1 + s)**3 == 7 + 5*s
proof = field_identity(quadratic_context(2), max_power=3)"

-- ℚ(√2): the rotation by 45° is orthogonal, entry by entry
example : !![Real.sqrt 2 / 2, -(Real.sqrt 2 / 2); Real.sqrt 2 / 2, Real.sqrt 2 / 2] *
    !![Real.sqrt 2 / 2, Real.sqrt 2 / 2; -(Real.sqrt 2 / 2), Real.sqrt 2 / 2] = 1 := by
  sage_run "
K = QuadraticField(2, 's'); s = K.gen()
R = matrix(K, [[s/2, -s/2], [s/2, s/2]])
check_matrix_identity(R * R.transpose(), identity_matrix(K, 2))
proof = field_matrix_identity(quadratic_context(2))"

-- ℚ(ζ₅): ζ + ζ⁴ is a root of x² + x - 1, from Φ₅(ζ) = 0, which IsPrimitiveRoot gives
example (ζ : ℂ) (hζ : IsPrimitiveRoot ζ 5) : (ζ + ζ ^ 4) ^ 2 + (ζ + ζ ^ 4) - 1 = 0 := by
  sage_run "
K = CyclotomicField(5, 'z'); z = K.gen()
assert (z + z**4)**2 + (z + z**4) - 1 == 0
proof = field_identity(cyclotomic_context(5), max_power=8)"

-- ℚ(α): an identity of rational functions in a parameter, with α ≠ 0
example (α : ℝ) (hα : α ≠ 0) : !![α, 1; 0, 1 / α] * !![1 / α, -1; 0, α] = 1 := by
  sage_run "
F = FractionField(QQ['a']); a = F.gen()
check_matrix_identity(matrix(F, [[a, 1], [0, 1/a]]) * matrix(F, [[1/a, -1], [0, a]]), identity_matrix(F, 2))
proof = field_matrix_identity(parameter_context('α'))"

/-! ## Representations, decompositions and intertwiners -/

-- the adjoint representation of 𝔰𝔩₃: eight 8×8 matrices satisfying every bracket relation of the algebra
set_option maxRecDepth 10000 in
example : True := by
  sage_run "
L = LieAlgebra(QQ, cartan_type=['A', 2], representation='matrix')
basis = [matrix(QQ, b.value) for b in L.basis()]
table = structure_constants(basis)
proof = steps(representation_relations(adjoint_matrices(table), table), tactic('trivial'))"

-- two spin-½: projectors onto spin 1 and spin 0, from the Casimir, commuting with the generators
example : True := by
  sage_run "
rho = tensor_representation(spin_representation(1), spin_representation(1))
e, f, h = rho
projectors = [p for _, p in eigen_projectors(e*f + f*e + h*h/2)]
assert sorted(p.rank() for p in projectors) == [1, 3]
proof = steps(projector_facts(projectors, rho), tactic('trivial'))"

-- the Clebsch–Gordan matrix of 1 ⊗ ½ intertwines the product with spin 3/2 ⊕ spin 1/2
example : True := by
  sage_run "
t, spins = clebsch_gordan(2, 1)
product = tensor_representation(spin_representation(2), spin_representation(1))
blocks = [block_diagonal_matrix([spin_representation(s)[k] for s in spins]) for k in range(3)]
proof = steps(intertwining_facts(t, product, blocks), tactic('trivial'))"

-- the 10 of SU(5) branches to (3̄,1) ⊕ (3,2) ⊕ (1,1) under SU(3)×SU(2)×U(1) embedded by blocks
set_option maxRecDepth 10000 in
example : True := by
  sage_run "
rho, labels = defining_representation('A4')
index = {label: i for i, label in enumerate(labels)}
subgroup = [rho[index[g]] for g in ['e1', 'e2', 'f1', 'f2', 'h1', 'h2', 'e4', 'f4', 'h4']]
subgroup.append(diagonal_matrix(QQ, [-2, -2, -2, 3, 3]))
wedge, pairs = exterior_square(subgroup)
def span(keep):
    return matrix(QQ, [[1 if k == pairs.index(q) else 0 for k in range(10)] for q in pairs if keep(q)]).transpose()
summands = [span(lambda q: q[1] < 3), span(lambda q: q[0] < 3 <= q[1]), span(lambda q: q[0] >= 3)]
assert [s.ncols() for s in summands] == [3, 6, 1]
p, blocks = decomposition(wedge, summands)
proof = steps(change_of_basis_facts(p, wedge, blocks), tactic('trivial'))"

/-! ## The `representation` recipe -/

-- the template unedited asks for the matrices
/--
error: sage daemon error: run: AssertionError: fill in REPRESENTATION (and TABLE, CASIMIR, SUMMANDS or TARGET) in a copy
-/
#guard_msgs in
example : True := by
  sage_run file "prompts/recipes/templates/representation.sage"

-- a copy for two spin-½: projectors onto spin 1 and spin 0
example : True := by
  sage_run file "rep_two_spins.sage"

/-! ## Lie superalgebras -/

namespace SuperTest

-- osp(1|2) on (1|2): the even coordinate first
def h : Matrix (Fin 3) (Fin 3) ℚ := !![0, 0, 0; 0, 1, 0; 0, 0, -1]
def e : Matrix (Fin 3) (Fin 3) ℚ := !![0, 0, 0; 0, 0, 1; 0, 0, 0]
def f : Matrix (Fin 3) (Fin 3) ℚ := !![0, 0, 0; 0, 0, 0; 0, 1, 0]
def qp : Matrix (Fin 3) (Fin 3) ℚ := !![0, 0, 1; 1, 0, 0; 0, 0, 0]
def qm : Matrix (Fin 3) (Fin 3) ℚ := !![0, -1, 0; 0, 0, 0; 1, 0, 0]

-- the graded brackets of osp(1|2): anticommutators of the odd generators, commutators otherwise
example : qp * qm + qm * qp = -h ∧ qp * qp + qp * qp = 2 • e ∧ e * qm - qm * e = qp := by
  sage_run "
def unit(i, j):
    m = matrix(QQ, 3, 3); m[i, j] = 1; return m
basis = [unit(1, 1) - unit(2, 2), unit(1, 2), unit(2, 1), unit(1, 0) + unit(0, 2), unit(2, 0) - unit(0, 1)]
parities = [parity_of(m, 1) for m in basis]
names = ['SuperTest.h', 'SuperTest.e', 'SuperTest.f', 'SuperTest.qp', 'SuperTest.qm']
proof = steps(super_relations(basis, parities, names), tactic('exact ⟨hs_3_4, hs_3_3, by simpa using hs_1_4⟩'))"

end SuperTest

-- D(2,1;α): the super-Jacobi identity for every real α, from kernel checks at α = 0, 1 and -1
set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
example : True := by
  sage_run "
t0, parities = d21_alpha(QQ(0))
t1p, _ = d21_alpha(QQ(1))
t1 = [[[t1p[i][j][k] - t0[i][j][k] for k in range(17)] for j in range(17)] for i in range(17)]
proof = steps(super_jacobi_family_certificate(t0, t1, parities), tactic('trivial'))"

-- G(3) = G₂ ⊕ 𝔰𝔩₂ on 7 ⊗ 2, with integral constants after rescaling the basis
set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
example : True := by
  sage_run "
table, parities = g3()
table, scales = integral_rescaling(table, parities)
proof = steps(super_jacobi_certificate(table, parities), tactic('trivial'))"

-- F(4) = so(7) ⊕ 𝔰𝔩₂ on 8 ⊗ 2 (40-dimensional): about a minute and a half of kernel checking
set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
example : True := by
  sage_run "
table, parities = f4()
table, scales = integral_rescaling(table, parities)
proof = steps(super_jacobi_certificate(table, parities), tactic('trivial'))"

/-! ## The `lie_superalgebra` recipe -/

-- the template unedited asks what to prove
/--
error: sage daemon error: run: AssertionError: fill in SUPERMATRICES (with EVEN_DIM and NAMES) or ALGEBRA in a copy
-/
#guard_msgs in
example : True := by
  sage_run file "prompts/recipes/templates/lie_superalgebra.sage"

-- a copy for osp(1|2) by name
example : SuperTest.qp * SuperTest.qm + SuperTest.qm * SuperTest.qp = -SuperTest.h ∧
    SuperTest.qp * SuperTest.qp + SuperTest.qp * SuperTest.qp = 2 • SuperTest.e := by
  sage_run file "osp12.sage"

-- a copy for D(2,1;α)
set_option maxRecDepth 100000 in
set_option maxHeartbeats 0 in
example : True := by
  sage_run file "lie_superalgebra_d21.sage"

/-! ## Matrix normal forms -/

-- a Smith normal form, with U and V unimodular (their integer inverses are checked too)
example : True := by
  sage_run "
d, u, v, facts = smith_certificate(matrix(ZZ, [[2, 4, 4], [-6, 6, 12], [10, -4, -16]]))
assert d.diagonal() == [2, 6, 12], d
proof = steps(facts, tactic('trivial'))"

-- a Jordan form with a nontrivial block: A * P = P * J and P invertible
example : True := by
  sage_run "
j, p, facts = jordan_certificate(matrix(QQ, [[5, 4, 2, 1], [0, 1, -1, -1], [-1, -1, 3, 0], [1, 1, -1, 2]]))
assert any(j[i, i + 1] != 0 for i in range(3)), j
proof = steps(facts, tactic('trivial'))"

/-! ## Matrix exponentials against mathlib's `exp` -/

-- a nilpotent matrix: the series stops
example : NormedSpace.exp (!![(0 : ℝ), 1, 2; 0, 0, 3; 0, 0, 0]) = !![1, 1, 7 / 2; 0, 1, 3; 0, 0, 1] := by
  sage_run "proof = nilpotent_exponential(matrix(QQ, [[0, 1, 2], [0, 0, 3], [0, 0, 0]]))[1]"

-- the Lorentz boost along x: exp of rapidity times the generator, through its diagonalization
example (φ : ℝ) : NormedSpace.exp (φ • !![(0 : ℝ), 1, 0, 0; 1, 0, 0, 0; 0, 0, 0, 0; 0, 0, 0, 0]) =
    !![Real.cosh φ, Real.sinh φ, 0, 0; Real.sinh φ, Real.cosh φ, 0, 0; 0, 0, 1, 0; 0, 0, 0, 1] := by
  sage_run "proof = diagonalizable_exponential(matrix(QQ, [[0, 1, 0, 0], [1, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]), 'φ')[1]"

/-! ## Algebraic recipes -/

example (x y : ℝ) (h1 : x ^ 2 + y ^ 2 < 1) (h2 : x + y ≥ 2) : False := by
  sage_run file "prompts/recipes/templates/infeasibility.sage"
example (x y : ℚ) (hxy : x * y = 1) (hx : x = 0) : False := by
  sage_run file "prompts/recipes/templates/infeasibility.sage"
example (x : ℝ) (h : x ^ 2 = 0) : x = 0 := by
  sage_run file "prompts/recipes/templates/infeasibility.sage"

-- a 40-digit prime
example : Nat.Prime 1000000000000000000000000000000000012397 := by
  sage_run file "prompts/recipes/templates/primality.sage"

/--
error: sage daemon error: run: AssertionError: fill in MATRIX (and FORM) in a copy
-/
#guard_msgs in
example : True := by
  sage_run file "prompts/recipes/templates/matrix_normal_form.sage"
example : True := by
  sage_run file "smith_example.sage"

/--
error: sage daemon error: run: AssertionError: fill in MATRIX (and PARAMETER) in a copy
-/
#guard_msgs in
example : True := by
  sage_run file "prompts/recipes/templates/matrix_exponential.sage"
example (φ : ℝ) : NormedSpace.exp (φ • !![(0 : ℝ), 1, 0, 0; 1, 0, 0, 0; 0, 0, 0, 0; 0, 0, 0, 0]) =
    !![Real.cosh φ, Real.sinh φ, 0, 0; Real.sinh φ, Real.cosh φ, 0, 0; 0, 0, 1, 0; 0, 0, 0, 1] := by
  sage_run file "boost.sage"

/-! ## Differential operators on a test function -/

-- [d/dx, x] = 1
example (ψ : ℝ → ℝ) (hψ : ContDiff ℝ 1 ψ) (x : ℝ) : deriv (fun y => y * ψ y) x - x * deriv ψ x = ψ x := by
  sage_run "
c = Coordinates(1)
d, xm = c.partial(0), c.multiplication(c.symbols[0])
proof = steps(operator_identity(commutator(d, xm), c.scalar(1), c), tactic('simpa using hop'))"

-- the ladder operators: [x + d/dx, x - d/dx] = 2
example (ψ : ℝ → ℝ) (hψ : ContDiff ℝ 2 ψ) (x : ℝ) : True := by
  sage_run "
c = Coordinates(1)
d, xm = c.partial(0), c.multiplication(c.symbols[0])
proof = steps(operator_identity(commutator(xm + d, xm - d), c.scalar(2), c), tactic('trivial'))"

-- angular momentum: [L₁, L₂] = -L₃ with Lᵢ = xⱼ ∂ₖ - xₖ ∂ⱼ, under ContDiff ℝ 2 (mixed partials commute)
example (ψ : (Fin 3 → ℝ) → ℝ) (hψ : ContDiff ℝ 2 ψ) (x : Fin 3 → ℝ) : True := by
  sage_run "
c = Coordinates(3)
def L(j, k):
    return c.multiplication(c.symbols[j]) * c.partial(k) - c.multiplication(c.symbols[k]) * c.partial(j)
proof = steps(operator_identity(commutator(L(1, 2), L(2, 0)), c.scalar(-1) * L(0, 1), c), tactic('trivial'))"

/-! ## Matrix operators -/

namespace OperatorTest

def σ₁ : Matrix (Fin 2) (Fin 2) ℂ := !![0, 1; 1, 0]
def σ₂ : Matrix (Fin 2) (Fin 2) ℂ := !![0, -Complex.I; Complex.I, 0]
def σ₃ : Matrix (Fin 2) (Fin 2) ℂ := !![1, 0; 0, -1]

-- the Pauli commutators [σᵢ, σⱼ] = 2i εᵢⱼₖ σₖ, from Sage's coefficients, proved entrywise over ℂ
example : σ₁ * σ₂ - σ₂ * σ₁ = (2 * Complex.I) • σ₃ ∧ σ₂ * σ₃ - σ₃ * σ₂ = (2 * Complex.I) • σ₁ ∧
    σ₃ * σ₁ - σ₁ * σ₃ = (2 * Complex.I) • σ₂ := by
  sage_run "
i = QuadraticField(-1, 'i').gen()
pauli = [matrix([[0, 1], [1, 0]]), matrix([[0, -i], [i, 0]]), matrix([[1, 0], [0, -1]])]
names = ['OperatorTest.σ₁', 'OperatorTest.σ₂', 'OperatorTest.σ₃']
proof = steps(operator_relations(pauli, names, pairs=[(0, 1), (1, 2), (2, 0)]),
              tactic('exact ⟨hcomm_0_1, hcomm_1_2, hcomm_2_0⟩'))"

end OperatorTest

-- truncated ladder operators on three levels: [a, a†] = 1 - 3 |2⟩⟨2|
example : True := by
  sage_run "
a, ad = ladder_matrices(3)
lhs, rhs = a * ad - ad * a, matrix(SR, [[1, 0, 0], [0, 1, 0], [0, 0, -2]])
assert lhs == rhs
statement = (real_matrix_term(a) + ' * ' + real_matrix_term(ad) + ' - ' + real_matrix_term(ad) + ' * ' +
             real_matrix_term(a) + ' = ' + real_matrix_term(rhs))
proof = steps(tactic('have hladder : ' + statement + ' := by\\n' +
                     '\\n'.join('  ' + l for l in matrix_identity_proof().text.splitlines())), tactic('trivial'))"
