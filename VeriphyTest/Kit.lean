/-
Sage-free tests of the kit: lenient problem extraction, closeAndEmit's checks, replay
and the axiom guard. `lake build VeriphyTest.Kit` needs no Sage.
-/
import Mathlib.Algebra.Order.Ring.Rat
import Mathlib.Tactic.Linarith
import Mathlib.Analysis.SpecialFunctions.Trigonometric.Basic
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
info: {"atoms":["Real.cos x","x","Real.sin x"],"carrier":"ℝ","goal":{"kind":"rel","lhs":"Real.cos x","lhs_poly":"x0","poly":"(x0) - (1)","rel":"le","rhs":"1","rhs_poly":"1","text":"Real.cos x ≤ 1"},"hyps":[{"name":"h","poly":"(x1) - (1)","rel":"le","text":"x ≤ 1"},{"name":"hs","poly":"(x2) - (1)","rel":"le","text":"Real.sin x ≤ 1"},{"name":"hn","text":"x ^ n ≤ 2"}],"vars":["x0","x1","x2"]}
-/
#guard_msgs (info, error, drop warning) in
example (x : ℝ) (h : x ≤ 1) (hs : Real.sin x ≤ 1) (n : ℕ) (hn : x ^ n ≤ 2) : Real.cos x ≤ 1 := by
  kit_lenient

-- lenient: an existential whose body translates keeps its binders
/--
info: {"atoms":["x","y"],"carrier":"ℚ","goal":{"binders":2,"body":[{"poly":"((x0 + x1)) - (1)","rel":"eq","text":"x + y = 1"},{"poly":"(x0) - (x1)","rel":"lt","text":"x < y"}],"kind":"exists"},"hyps":[],"vars":["x0","x1"]}
-/
#guard_msgs (info, error, drop warning) in
example : ∃ x y : ℚ, x + y = 1 ∧ x < y := by
  kit_lenient

-- lenient: a goal with no polynomial form is kept as text, with the hypotheses still collected
/--
info: {"atoms":["x"],"carrier":"ℤ","goal":{"kind":"other","text":"x ∣ 6"},"hyps":[{"name":"h","poly":"(x0) - (2)","rel":"eq","text":"x = 2"}],"vars":["x0"]}
-/
#guard_msgs (info, error, drop warning) in
example (x : ℤ) (h : x = 2) : x ∣ 6 := by
  kit_lenient

-- `≥` flips, `¬ (v = 0)` is `≠`, an inaccessible hypothesis is never offered, a hypothesis over
-- another carrier is kept as text
/--
info: {"atoms":["x","y"],"carrier":"ℚ","goal":{"kind":"rel","lhs":"x","lhs_poly":"x0","poly":"(x0) - ((x1 + x0))","rel":"le","rhs":"y + x","rhs_poly":"(x1 + x0)","text":"x ≤ y + x"},"hyps":[{"name":"h1","poly":"(x1) - (x0)","rel":"le","text":"x ≥ y"},{"name":"h2","poly":"(x0) - (0)","rel":"ne","text":"¬x = 0"},{"name":"hn","text":"n = 3"}],"vars":["x0","x1"]}
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
