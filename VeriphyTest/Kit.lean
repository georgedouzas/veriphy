/-
Sage-free tests of the kit: lenient problem extraction, closeAndEmit's checks, replay
and the axiom guard. `lake build VeriphyTest.Kit` needs no Sage.
-/
import Mathlib.Algebra.Order.Ring.Rat
import Mathlib.Tactic.Linarith
import Mathlib.Analysis.SpecialFunctions.Trigonometric.Basic
import Mathlib.Analysis.SpecialFunctions.Pow.Real
import Mathlib.Analysis.SpecialFunctions.Log.Basic
import Mathlib.LinearAlgebra.Matrix.Notation
import Mathlib.LinearAlgebra.Matrix.Determinant.Basic
import Mathlib.Algebra.Polynomial.Eval.Defs
import Mathlib.Analysis.SpecialFunctions.Gamma.Basic
import Veriphy.Kit

open Lean Elab Tactic Meta Veriphy

set_option linter.unusedVariables false
set_option linter.unusedTactic false

/-! ## Problem extraction (lenient) -/

/-- Test tactic: lenient extraction, printing the serialized problem, then admit the goal. -/
elab "kit_lenient" : tactic => do
  let j ← withLenientProblem fun p => p.toJson
  logInfo m!"{j.compress}"
  (← getMainGoal).admit (synthetic := true)

-- lenient: function applications are atoms; a hypothesis with no polynomial form (`x ^ n`) is kept as text
/--
info: {"atom_types":["ℝ","ℝ","ℝ","ℕ"],"atoms":["Real.cos x","x","Real.sin x","n"],"carrier":"ℝ","domain":[],"goal":{"expr":"(cos(x1)) - (1)","kind":"rel","lhs":"Real.cos x","lhs_poly":"x0","poly":"(x0) - (1)","rel":"le","rhs":"1","rhs_poly":"1","text":"Real.cos x ≤ 1"},"hyps":[{"expr":"(x1) - (1)","name":"h","poly":"(x1) - (1)","rel":"le","text":"x ≤ 1"},{"expr":"(sin(x1)) - (1)","name":"hs","poly":"(x2) - (1)","rel":"le","text":"Real.sin x ≤ 1"},{"expr":"((x1)^(x3)) - (2)","name":"hn","rel":"le","text":"x ^ n ≤ 2"}],"vars":["x0","x1","x2","x3"]}
-/
#guard_msgs (info, error, drop warning) in
example (x : ℝ) (h : x ≤ 1) (hs : Real.sin x ≤ 1) (n : ℕ) (hn : x ^ n ≤ 2) : Real.cos x ≤ 1 := by
  kit_lenient

-- lenient: an existential whose body translates keeps its binders
/--
info: {"atom_types":["ℚ","ℚ"],"atoms":["x","y"],"carrier":"ℚ","domain":[],"goal":{"binders":2,"body":[{"expr":"((x0 + x1)) - (1)","poly":"((x0 + x1)) - (1)","rel":"eq","text":"x + y = 1"},{"expr":"(x0) - (x1)","poly":"(x0) - (x1)","rel":"lt","text":"x < y"}],"kind":"exists"},"hyps":[],"vars":["x0","x1"]}
-/
#guard_msgs (info, error, drop warning) in
example : ∃ x y : ℚ, x + y = 1 ∧ x < y := by
  kit_lenient

-- lenient: a goal with no polynomial form is kept as text, with the hypotheses still collected
/--
info: {"atom_types":["ℤ"],"atoms":["x"],"carrier":"ℤ","domain":[],"goal":{"kind":"other","text":"x ∣ 6"},"hyps":[{"expr":"(x0) - (2)","name":"h","poly":"(x0) - (2)","rel":"eq","text":"x = 2"}],"vars":["x0"]}
-/
#guard_msgs (info, error, drop warning) in
example (x : ℤ) (h : x = 2) : x ∣ 6 := by
  kit_lenient

-- `≥` flips, `¬ (v = 0)` is `≠`, an inaccessible hypothesis is never offered, a hypothesis over
-- another carrier is kept as text
/--
info: {"atom_types":["ℚ","ℚ","ℕ"],"atoms":["x","y","n"],"carrier":"ℚ","domain":[],"goal":{"expr":"(x0) - ((x1 + x0))","kind":"rel","lhs":"x","lhs_poly":"x0","poly":"(x0) - ((x1 + x0))","rel":"le","rhs":"y + x","rhs_poly":"(x1 + x0)","text":"x ≤ y + x"},"hyps":[{"expr":"(x1) - (x0)","name":"h1","poly":"(x1) - (x0)","rel":"le","text":"x ≥ y"},{"expr":"(x0) - (0)","name":"h2","poly":"(x0) - (0)","rel":"ne","text":"¬x = 0"},{"expr":"(x2) - (3)","name":"hn","rel":"eq","text":"n = 3"}],"vars":["x0","x1","x2"]}
-/
#guard_msgs (info, error, drop warning) in
example (x y : ℚ) (n : ℕ) (hn : n = 3) (h1 : x ≥ y) (h2 : ¬ (x = 0)) : y = x → x ≤ y + x := by
  intro
  kit_lenient

/-! ## Replay -/

set_option veriphy.checkReplay true

/-- A deliberately hygienic proof: runs fine, but prints `hk✝`. -/
elab "kit_hygienic" : tactic => do
  closeAndEmit (← `(tactic| (have hk : (0 : ℚ) ≤ 1 := (by norm_num); exact hk)))

/-- A "replacement" that calls the bridge (a stand-in for a leaked `sage_*` call). -/
elab "kit_calls_sage" : tactic => do
  Kit.run "test" (pure ())
  evalTactic (← `(tactic| norm_num))

elab "kit_leaky" : tactic => do
  closeAndEmit (← `(tactic| kit_calls_sage))

/--
error: veriphy replay: the printed replacement does not re-parse (<input>:1:8: expected token):
(have hk✝ : (0 : ℚ) ≤ 1 := (by norm_num); exact hk✝)
-/
#guard_msgs in
example : (0 : ℚ) ≤ 1 := by kit_hygienic

/--
error: veriphy replay: the printed replacement does not reproduce the proof — it fails: veriphy: the Sage bridge is disabled during replay, but the replacement called Sage (test); a committed proof must not need Sage
replacement:
kit_calls_sage
-/
#guard_msgs in
example : (0 : ℚ) ≤ 1 := by kit_leaky

-- replay off: the same hygienic proof is accepted (this is the bug class replay exists to catch)
set_option veriphy.checkReplay false in
#guard_msgs (drop info) in
example : (0 : ℚ) ≤ 1 := by kit_hygienic

/-! ## Axiom guard -/

/-- Test tactic: run any tactic through `closeAndEmit`. -/
elab "kit_emit " t:tactic : tactic => closeAndEmit t

/-- error: veriphy: the proof uses `sorry` (sorryAx); only fully checked proofs are accepted -/
#guard_msgs in
example : (2 : ℕ) + 2 = 4 := by kit_emit sorry

/--
error: veriphy: the proof depends on the axiom `_example._native.native_decide.ax_1`; only `propext`, `Classical.choice` and `Quot.sound` are accepted
-/
#guard_msgs in
example : (2 : ℕ) + 2 = 4 := by kit_emit native_decide

/-- info: Sage-free replacement: 
  [apply] decide -/
#guard_msgs in
example : (2 : ℕ) + 2 = 4 := by kit_emit decide

-- classical reasoning stays allowed
#guard_msgs (drop info) in
example (p : Prop) : p ∨ ¬p := by kit_emit exact Classical.em p


/-! ## closeAndEmit -/

-- a failure inside a nested `by` fails the tactic (it is not just logged), and nothing is emitted
example : (1 : ℚ) ≤ 2 := by
  fail_if_success kit_emit (have h : (2 : ℚ) ≤ 1 := by norm_num
                            exact absurd h (by norm_num))
  norm_num

/-! ## Symbolic translation -/

-- one rendering per constructor
/--
info: (-3/2)
x1
(x0 + 1)
(x0 - x1)
(x0 * x1)
(1 / x0)
(-x0)
(x0)^(x1)
mod(x0, 3)
sqrt(x0)
pi
sum((k_)^(2), k_, 0, x0 - 1)
product(k_, k_, 0, x0 - 1)
matrix(SR, [[1, x0], [0, 1]])
(matrix(SR, [[x0]])).det()
-/
#guard_msgs in
run_elab do
  let k := SymExpr.bvar "k_"
  let terms : List SymExpr := [.num (-3) 2, .atom 1, .add (.atom 0) (.num 1 1), .sub (.atom 0) (.atom 1),
    .mul (.atom 0) (.atom 1), .div (.num 1 1) (.atom 0), .neg (.atom 0), .pow (.atom 0) (.atom 1),
    .mod (.atom 0) (.num 3 1), .fn "sqrt" (.atom 0), .const "pi", .rangeOp true "k_" (.atom 0) (.pow k (.num 2 1)),
    .rangeOp false "k_" (.atom 0) k, .matrix [[.num 1 1, .atom 0], [.num 0 1, .num 1 1]],
    .method "det" (.matrix [[.atom 0]]) []]
  logInfo m!"{"\n".intercalate (terms.map (·.toSage))}"

-- rational function; the denominator condition is discharged by `hy`
/--
info: {"atom_types":["ℝ","ℝ","ℝ","ℝ"],"atoms":["x / y","1 / (x ^ 2 + 1)","y","x"],"carrier":"ℝ","domain":[{"discharged_by":"hy","expr":"x2","kind":"ne","text":"y ≠ 0"},{"expr":"((x3)^(2) + 1)","kind":"ne","text":"x ^ 2 + 1 ≠ 0"}],"goal":{"expr":"(((x3 / x2) + (1 / ((x3)^(2) + 1)))) - (2)","kind":"rel","lhs":"x / y + 1 / (x ^ 2 + 1)","lhs_poly":"(x0 + x1)","poly":"((x0 + x1)) - (2)","rel":"le","rhs":"2","rhs_poly":"2","text":"x / y + 1 / (x ^ 2 + 1) ≤ 2"},"hyps":[{"expr":"(x2) - (0)","name":"hy","poly":"(x2) - (0)","rel":"ne","text":"y ≠ 0"}],"vars":["x0","x1","x2","x3"]}
-/
#guard_msgs (info, error, drop warning) in
example (x y : ℝ) (hy : y ≠ 0) : x / y + 1 / (x ^ 2 + 1) ≤ 2 := by kit_lenient

-- sqrt discharged by a nonnegativity hypothesis; log undischarged
/--
info: {"atom_types":["ℝ","ℝ","ℝ","ℝ"],"atoms":["√u","Real.log v","u","v"],"carrier":"ℝ","domain":[{"discharged_by":"hu","expr":"x2","kind":"nonneg","text":"0 ≤ u"},{"expr":"x3","kind":"pos","text":"0 < v"}],"goal":{"expr":"(0) - ((sqrt(x2) + log(x3)))","kind":"rel","lhs":"0","lhs_poly":"0","poly":"(0) - ((x0 + x1))","rel":"le","rhs":"√u + Real.log v","rhs_poly":"(x0 + x1)","text":"√u + Real.log v ≥ 0"},"hyps":[{"expr":"(0) - (x2)","name":"hu","poly":"(0) - (x2)","rel":"le","text":"0 ≤ u"}],"vars":["x0","x1","x2","x3"]}
-/
#guard_msgs (info, error, drop warning) in
example (u v : ℝ) (hu : 0 ≤ u) : Real.sqrt u + Real.log v ≥ 0 := by kit_lenient

-- transcendental identity: the atoms are a and b, not exp a
/--
info: {"atom_types":["ℝ","ℝ","ℝ","ℝ","ℝ"],"atoms":["Real.exp a","Real.exp b","Real.exp (a + b)","a","b"],"carrier":"ℝ","domain":[],"goal":{"expr":"((exp(x3) * exp(x4))) - (exp((x3 + x4)))","kind":"rel","lhs":"Real.exp a * Real.exp b","lhs_poly":"(x0 * x1)","poly":"((x0 * x1)) - (x2)","rel":"eq","rhs":"Real.exp (a + b)","rhs_poly":"x2","text":"Real.exp a * Real.exp b = Real.exp (a + b)"},"hyps":[],"vars":["x0","x1","x2","x3","x4"]}
-/
#guard_msgs (info, error, drop warning) in
example (a b : ℝ) : Real.exp a * Real.exp b = Real.exp (a + b) := by kit_lenient

-- abs over ℝ, ℂ and ℤ; casts from ℕ; pi and I
/--
info: {"atom_types":["ℝ","ℝ","ℝ","ℝ","ℝ","ℤ","ℕ"],"atoms":["|x - 1|","|↑k|","↑n","Real.pi","x","k","n"],"carrier":"ℝ","domain":[],"goal":{"expr":"((abs((x4 - 1)) + abs(x5))) - ((x6 * pi))","kind":"rel","lhs":"|x - 1| + |↑k|","lhs_poly":"(x0 + x1)","poly":"((x0 + x1)) - ((x2 * x3))","rel":"le","rhs":"↑n * Real.pi","rhs_poly":"(x2 * x3)","text":"|x - 1| + |↑k| ≤ ↑n * Real.pi"},"hyps":[],"vars":["x0","x1","x2","x3","x4","x5","x6"]}
-/
#guard_msgs (info, error, drop warning) in
example (x : ℝ) (k : ℤ) (n : ℕ) : |x - 1| + |(k : ℝ)| ≤ (n : ℝ) * Real.pi := by kit_lenient
/--
info: {"atom_types":["ℤ","ℤ"],"atoms":["|k|","k"],"carrier":"ℤ","domain":[],"goal":{"expr":"(abs(x1)) - ((x1)^(2))","kind":"rel","lhs":"|k|","lhs_poly":"x0","poly":"(x0) - ((x1)^2)","rel":"le","rhs":"k ^ 2","rhs_poly":"(x1)^2","text":"|k| ≤ k ^ 2"},"hyps":[],"vars":["x0","x1"]}
-/
#guard_msgs (info, error, drop warning) in
example (k : ℤ) : |k| ≤ k ^ 2 := by kit_lenient
/--
info: {"atom_types":["ℂ","ℂ"],"atoms":["z","Complex.I"],"carrier":"ℂ","domain":[],"goal":{"expr":"((x0 * I)) - ((I * x0))","kind":"rel","lhs":"z * Complex.I","lhs_poly":"(x0 * x1)","poly":"((x0 * x1)) - ((x1 * x0))","rel":"eq","rhs":"Complex.I * z","rhs_poly":"(x1 * x0)","text":"z * Complex.I = Complex.I * z"},"hyps":[],"vars":["x0","x1"]}
-/
#guard_msgs (info, error, drop warning) in
example (z : ℂ) : z * Complex.I = Complex.I * z := by kit_lenient

-- range sum, mod, matrix literal and determinant, polynomial evaluation
/--
info: {"atom_types":["ℚ","ℚ","ℕ"],"atoms":["∑ i ∈ Finset.range n, ↑i ^ 2","↑(n % 7)","n"],"carrier":"ℚ","domain":[],"goal":{"expr":"(sum((i_)^(2), i_, 0, x2 - 1)) - (mod(x2, 7))","kind":"rel","lhs":"∑ i ∈ Finset.range n, ↑i ^ 2","lhs_poly":"x0","poly":"(x0) - (x1)","rel":"eq","rhs":"↑(n % 7)","rhs_poly":"x1","text":"∑ i ∈ Finset.range n, ↑i ^ 2 = ↑(n % 7)"},"hyps":[],"vars":["x0","x1","x2"]}
-/
#guard_msgs (info, error, drop warning) in
example (n : ℕ) : ∑ i ∈ Finset.range n, (i : ℚ) ^ 2 = (n % 7 : ℕ) := by kit_lenient
/--
info: {"atom_types":["ℚ","ℚ"],"atoms":["!![1, c; 0, 1].det","c"],"carrier":"ℚ","domain":[],"goal":{"expr":"((matrix(SR, [[1, x1], [0, 1]])).det()) - (1)","kind":"rel","lhs":"!![1, c; 0, 1].det","lhs_poly":"x0","poly":"(x0) - (1)","rel":"eq","rhs":"1","rhs_poly":"1","text":"!![1, c; 0, 1].det = 1"},"hyps":[],"vars":["x0","x1"]}
-/
#guard_msgs (info, error, drop warning) in
example (c : ℚ) : Matrix.det !![(1 : ℚ), c; 0, 1] = 1 := by kit_lenient
/--
info: {"atom_types":["ℚ","ℚ"],"atoms":["Polynomial.eval x (Polynomial.X ^ 2 + Polynomial.C 1)","x"],"carrier":"ℚ","domain":[],"goal":{"expr":"((((X)^(2) + 1)).subs(X=x1)) - (((x1)^(2) + 1))","kind":"rel","lhs":"Polynomial.eval x (Polynomial.X ^ 2 + Polynomial.C 1)","lhs_poly":"x0","poly":"(x0) - (((x1)^2 + 1))","rel":"eq","rhs":"x ^ 2 + 1","rhs_poly":"((x1)^2 + 1)","text":"Polynomial.eval x (Polynomial.X ^ 2 + Polynomial.C 1) = x ^ 2 + 1"},"hyps":[],"vars":["x0","x1"]}
-/
#guard_msgs (info, error, drop warning) in
example (x : ℚ) : (Polynomial.X ^ 2 + Polynomial.C 1 : Polynomial ℚ).eval x = x ^ 2 + 1 := by kit_lenient

/-! ## Project layout -/

-- a bare name lives in `.veriphy/certificates/`, other paths come from the workspace root, from any subdirectory
/-- info: [true, true, true, true] -/
#guard_msgs in
#eval show IO (List Bool) from do
  let root ← IO.currentDir
  let sub := root / "VeriphyTest"
  return [
    (← Veriphy.workspaceRoot (some sub)) == root,
    (← Veriphy.resolveScriptPath "anomaly.sage" (some sub)) == root / ".veriphy" / "certificates" / "anomaly.sage",
    (← Veriphy.resolveScriptPath ".veriphy/certificates/anomaly.sage" (some sub)) ==
      root / ".veriphy/certificates/anomaly.sage",
    (← Veriphy.resolveScriptPath "prompts/recipes/templates/sos.sage") ==
      root / "prompts/recipes/templates/sos.sage"]

-- a missing script is reported with its resolved path, before any daemon call
/-- info: true -/
#guard_msgs in
#eval show IO Bool from do
  try
    let _ ← Veriphy.readScript "no_such_script.sage"
    return false
  catch e =>
    return (e.toString.splitOn ".veriphy/certificates/no_such_script.sage").length > 1

/-! ## Coverage measurement -/

namespace CoverageFixture
theorem full (x : ℝ) (hx : 0 < x) : Real.log (x ^ 2) = 2 * Real.log x := by
  rw [Real.log_pow]; norm_num
theorem gamma (x : ℝ) (hx : 0 < x) : 0 < Real.Gamma x := Real.Gamma_pos_of_pos hx
theorem uninterpreted (f : ℝ → ℝ) (x : ℝ) : f x ≤ f x + 1 := by linarith
theorem noRelation (f : ℝ → ℝ) (h : Continuous f) : Continuous f := h
theorem nested (a : ℝ) : (∃ b : ℝ, b ^ 2 = a) → 0 ≤ a := by
  rintro ⟨b, rfl⟩; positivity
end CoverageFixture

/--
info: theorems: 5, with a relation: 4, failed: 0
fully covered: 2 (50.0%)
covered up to uninterpreted functions: 3 (75.0%)
opaque heads:
  1  Real.Gamma  (e.g. CoverageFixture.gamma)
-/
#guard_msgs in
set_option veriphy.coverage.write false in
#veriphy_coverage [CoverageFixture]

-- the JSON report carries the same numbers and the ranked heads
#guard_msgs (drop info) in
#veriphy_coverage [CoverageFixture] ".lake/veriphy-coverage-test.json"

/-- info: [5, 4, 1, 2, 3, 0] Real.Gamma -/
#guard_msgs in
#eval show IO Unit from do
  let j ← IO.ofExcept (Lean.Json.parse (← IO.FS.readFile ".lake/veriphy-coverage-test.json"))
  let num (k : String) : Nat := ((j.getObjValAs? Nat k).toOption).getD 999
  let head := ((j.getObjValAs? (Array Lean.Json) "opaque_heads").toOption.bind (·[0]?)).bind
    (fun h => (h.getObjValAs? String "head").toOption)
  IO.println s!"{[num "theorems", num "with_relation", num "no_relation", num "fully_covered",
    num "covered_up_to_uninterpreted", num "failed"]} {head.getD "none"}"

/-! ## Translation tables -/

-- the Python toolkit's copy of the core table is the Lean one
/-- info: true -/
#guard_msgs in
#eval show IO Bool from do
  let j ← IO.ofExcept (Lean.Json.parse (← IO.FS.readFile "src/veriphy/toolkit/core_table.json"))
  let t ← IO.ofExcept (Lean.fromJson? (α := Veriphy.Table) j)
  return t == Veriphy.coreTable
