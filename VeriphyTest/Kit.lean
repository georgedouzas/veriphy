/-
Sage-free tests of the certificate kit: builders, problem extraction, families and
replay, fed literal certificates. `lake build VeriphyTest.Kit` needs no Sage.
-/
import Mathlib.Algebra.Order.Ring.Rat
import Mathlib.Tactic.Linarith
import Mathlib.Analysis.SpecialFunctions.Trigonometric.Basic
import Veriphy.Kit

open Lean Elab Tactic Meta Veriphy

set_option linter.unusedVariables false
set_option linter.unusedTactic false

/-! ## Builders -/

/-- info: -(3 / 2) -/
#guard_msgs in
run_elab do logInfo m!"{← ratStx' "-3/2"}"

/-- error: veriphy: bad rational in certificate: 1.5 -/
#guard_msgs in
run_elab do discard <| ratStx' "1.5"

/-- info: x ^ 2 * z -/
#guard_msgs in
run_elab do
  let atoms ← #[`x, `y, `z].mapM fun n => `($(mkIdent n))
  logInfo m!"{← polyStx atoms [{ coeff := "1", exps := [2, 0, 1] }]}"

/-- info: 0 -/
#guard_msgs in
run_elab do logInfo m!"{← polyStx #[] []}"

-- zero weights dropped, unit weights omitted, no hygiene markers
/-- info: h2 + (1 / 3) * h3 + (-2) * h4 -/
#guard_msgs in
run_elab do
  let hs := #[`h1, `h2, `h3, `h4].map fun n => (⟨(mkIdent n).raw⟩ : TSyntax `term)
  let ws := #["0", "1", "1/3", "-2"].map Bridge.Term.const
  logInfo m!"{← weightedSum #[] (ws.zip hs)}"

/-- error: veriphy: empty certificate (every weight is zero) -/
#guard_msgs in
run_elab do
  discard <| weightedSum #[] #[(Bridge.Term.const "0", ⟨(mkIdent `h).raw⟩)]

/-- error: veriphy: witness has 3 values for 2 binders -/
#guard_msgs in
run_elab do discard <| witnessStx ["1", "2", "3"] 2 (← `(trivial))

/-- info: ⟨1, -(1 / 2), by norm_num⟩ -/
#guard_msgs in
run_elab do logInfo m!"{← witnessStx ["1", "-1/2"] 2 (← `(by norm_num))}"

-- fresh names avoid the context and carry no macro scopes
/-- info: hfarkas_1 -/
#guard_msgs in
example (hfarkas : True) : True := by
  run_tac do withMainContext do logInfo m!"{← freshIdent `hfarkas}"
  trivial

/-- info: ( by_contra hfarkas
  simp only [not_le] at hfarkas) -/
#guard_msgs in
run_elab do
  let hn := mkIdent `hfarkas
  let s1 ← `(tactic| by_contra $hn:ident)
  let s2 ← `(tactic| simp only [$(mkIdent ``not_le):ident] at $hn:ident)
  logInfo m!"{← stepsStx #[s1, s2]}"

/-! ## Problem extraction -/

/-- Test tactic: extract with a preset and print the serialized problem, then admit the goal. -/
elab "kit_extract " preset:str : tactic => do
  let o : ExtractOpts := match preset.getString with
    | "lincomb" => { tac := "kit", goalRels := #[.eq], hypRels := #[.eq] }
    | "farkas" => { tac := "kit", allowFalse := true, hypRels := #[.eq, .le, .lt],
                    negateGoalAs := some `hfarkas }
    | "exists" => { tac := "kit", allowExists := true }
    | _ => { tac := "kit", goalRels := #[.eq, .le, .lt, .ne], allowFalse := true,
             hypRels := #[.eq, .le, .lt, .ne] }
  let j ← withProblem o fun p => p.toJson
  logInfo m!"{j.compress}"
  (← getMainGoal).admit (synthetic := true)

/-- Test tactic: lenient extraction, printing the serialized problem, then admit the goal. -/
elab "kit_lenient" : tactic => do
  let j ← withLenientProblem fun p => p.toJson
  logInfo m!"{j.compress}"
  (← getMainGoal).admit (synthetic := true)

-- lenient: function applications are atoms; a hypothesis with no polynomial form (`x ^ n`) is kept as text
/--
info: {"atoms":["Real.cos x","x","Real.sin x"],"carrier":"ℝ","goal":{"kind":"rel","poly":"(x0) - (1)","rel":"le","text":"Real.cos x ≤ 1"},"hyps":[{"name":"h","poly":"(x1) - (1)","rel":"le","text":"x ≤ 1"},{"name":"hs","poly":"(x2) - (1)","rel":"le","text":"Real.sin x ≤ 1"},{"name":"hn","text":"x ^ n ≤ 2"}],"vars":["x0","x1","x2"]}
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

-- `≥` flips; the atom shared by goal and hypothesis appears once
/--
info: {"atoms":["x"],"carrier":"ℚ","goal":{"kind":"rel","poly":"((x0)^2) - (4)","rel":"eq"},"hyps":[{"name":"h","poly":"(x0) - (2)","rel":"le"},{"name":"h'","poly":"(2) - (x0)","rel":"le"}],"vars":["x0"]}
-/
#guard_msgs (info, error, drop warning) in
example (x : ℚ) (h : x ≤ 2) (h' : x ≥ 2) : x ^ 2 = 4 := by kit_extract "all"

/--
info: {"atoms":["f a"],"carrier":"ℚ","goal":{"kind":"rel","poly":"((x0)^2) - (1)","rel":"eq"},"hyps":[{"name":"h","poly":"(x0) - (1)","rel":"eq"}],"vars":["x0"]}
-/
#guard_msgs (info, error, drop warning) in
example (f : ℚ → ℚ) (a : ℚ) (h : f a = 1) : f a ^ 2 = 1 := by kit_extract "lincomb"

-- `¬ (v = 0)` is `≠`
/--
info: {"atoms":["v"],"carrier":"ℚ","goal":{"kind":"false"},"hyps":[{"name":"hv","poly":"(x0) - (0)","rel":"ne"}],"vars":["x0"]}
-/
#guard_msgs (info, error, drop warning) in
example (v : ℚ) (hv : ¬ (v = 0)) : False := by kit_extract "all"

-- untranslatable hypothesis skipped cleanly (no atom from it); other carriers ignored; inaccessible names excluded
/--
info: {"atoms":["x","y"],"carrier":"ℚ","goal":{"kind":"rel","poly":"(x0) - (x1)","rel":"eq"},"hyps":[{"name":"h1","poly":"((x0 + x1)) - (1)","rel":"eq"}],"vars":["x0","x1"]}
-/
#guard_msgs (info, error, drop warning) in
example (x y : ℚ) (n : ℕ) (hn : n = 3) (h1 : x + y = 1) (h2 : x ^ n = 0) : y = x → x = y := by
  intro
  kit_extract "lincomb"

-- refutation preset: the negated goal becomes the last hypothesis, the goal `False`
/--
info: {"atoms":["u","v"],"carrier":"ℚ","goal":{"kind":"false"},"hyps":[{"name":"h1","poly":"(0) - (x0)","rel":"le"},{"name":"h2","poly":"((x0 + x1)) - (0)","rel":"eq"},{"name":"hfarkas","poly":"(0) - (x0)","rel":"lt"}],"vars":["x0","x1"]}
-/
#guard_msgs (info, error, drop warning) in
example (u v : ℚ) (h1 : 0 ≤ u) (h2 : u + v = 0) : u ≤ 0 := by kit_extract "farkas"

-- existential: binders are atoms 0, 1; conjuncts split
/--
info: {"atoms":["x","y"],"carrier":"ℚ","goal":{"binders":2,"body":[{"poly":"((x0 + x1)) - (1)","rel":"eq"},{"poly":"(0) - (x0)","rel":"lt"},{"poly":"(x0) - (x1)","rel":"lt"}],"kind":"exists"},"hyps":[],"vars":["x0","x1"]}
-/
#guard_msgs (info, error, drop warning) in
example : ∃ x y : ℚ, x + y = 1 ∧ 0 < x ∧ x < y := by kit_extract "exists"

/-- error: kit: the body has free subterms other than the bound variables -/
#guard_msgs (info, error, drop warning) in
example (a : ℚ) : ∃ x : ℚ, x = a := by kit_extract "exists"

/-- error: kit: goal must be `a = b`, got
  x ∣ y -/
#guard_msgs (info, error, drop warning) in
example (x y : ℤ) : x ∣ y := by kit_extract "lincomb"

/-! ## Checker families, fed literal certificates -/

/-- Test tactics: close the goal through a family with a literal certificate. -/
elab "kit_lincomb " combo:term : tactic => do
  closeAndEmit (← Checker.linearCombination combo)

elab "kit_refute " combo:term " kappa " k:str strict:(" strict")? : tactic => do
  let h ← withMainContext (freshIdent `hfarkas)
  let pre ← if (← whnfR (← getMainTarget)).isConstOf ``False then pure #[] else Checker.negateGoal h
  let combo ← combo.raw.replaceM fun s => pure <|
    if s.isIdent && s.getId == `NEG then some (mkIdent h.getId).raw else none
  closeAndEmit (← Checker.refute pre (← `(ℚ)) k.getString strict.isSome ⟨combo⟩)

/-- Number of leading `∃` binders. -/
partial def existsBinders (e : Expr) : Nat :=
  match e.getAppFnArgs with
  | (``Exists, #[_, .lam _ _ b _]) => 1 + existsBinders b
  | _ => 0

elab "kit_witness " vs:str* : tactic => do
  closeAndEmit (← Checker.witness (vs.toList.map (·.getString)) (existsBinders (← getMainTarget)))

elab "kit_sum " n:ident : tactic => do closeAndEmit (← Checker.sumInduction n)

elab "kit_decide" : tactic => do closeAndEmit (← Checker.cases)

set_option veriphy.checkReplay true

-- identity: ideal-membership certificate checked by linear_combination
/--
info: Sage-free replacement: 
  [apply] linear_combination (a + b + 3) * h - 2 * h'
-/
#guard_msgs in
example (a b : ℚ) (h : a + b = 3) (h' : a * b = 2) : a ^ 2 + b ^ 2 = 5 := by
  kit_lincomb (a + b + 3) * h - 2 * h'

-- wrong cofactors: the checker rejects, nothing is emitted, the goal is unchanged
/--
info: Sage-free replacement: 
  [apply] linear_combination (a + b + 3) * h - 2 * h'
-/
#guard_msgs in
example (a b : ℚ) (h : a + b = 3) (h' : a * b = 2) : a ^ 2 + b ^ 2 = 5 := by
  fail_if_success kit_lincomb (a + b) * h
  kit_lincomb (a + b + 3) * h - 2 * h'

-- inequality: a weighted square
/--
info: Sage-free replacement: 
  [apply] linear_combination sq_nonneg (x - y)
-/
#guard_msgs in
example (x y : ℚ) : 2 * x * y ≤ x ^ 2 + y ^ 2 := by kit_lincomb sq_nonneg (x - y)

-- a negative weight on an inequality: positivity cannot certify it
example (x : ℚ) (h1 : 0 ≤ x) : 0 ≤ x := by
  fail_if_success kit_lincomb (-1) * h1
  exact h1

-- inequality, refutation form from `False`
/--
info: Sage-free replacement: 
  [apply] (
    have hfk : (2 : ℚ) ≤ 0 := by linear_combination h1 - h2 + 2 * h3
    norm_num at hfk)
-/
#guard_msgs in
example (x y : ℚ) (h1 : x + y ≤ 1) (h2 : x - y = 3) (h3 : 0 ≤ y) : False := by
  kit_refute h1 - h2 + 2 * h3 kappa "2"

-- a wrong refutation certificate fails inside the nested `have … := by`: the tactic must fail
example (x y : ℚ) (h1 : x + y ≤ 1) (h2 : x - y = 3) (h3 : 0 ≤ y) : False := by
  fail_if_success kit_refute h1 + h3 + 1 / 2 * h2 kappa "1"
  linarith

-- refutation of a `≤` goal: negation step with a fresh, printable name
/--
info: Sage-free replacement: 
  [apply] (
    by_contra hfarkas
    simp only [not_le, not_lt, ge_iff_le, gt_iff_lt] at hfarkas
    have hfk : (0 : ℚ) < 0 := by linear_combination h2 + h3 + hfarkas
    norm_num at hfk)
-/
#guard_msgs in
example (u v : ℚ) (h1 : 0 ≤ u) (h2 : u + v = 0) (h3 : 0 ≤ v) : u ≤ 0 := by
  kit_refute h2 + h3 + NEG kappa "0" strict

-- witness
/--
info: Sage-free replacement: 
  [apply] exact ⟨1, 1, by norm_num⟩
-/
#guard_msgs in
example : ∃ v₁ v₂ : ℚ, 2 * v₁ + v₂ = 3 * v₁ ∧ v₁ + 2 * v₂ = 3 * v₂ ∧ v₁ ≠ 0 := by
  kit_witness "1" "1"

/-- error: veriphy: witness has 1 values for 2 binders -/
#guard_msgs in
example : ∃ x y : ℚ, x = y := by kit_witness "1"

-- sum: no oracle data at all
#guard_msgs (drop info) in
example (n : ℕ) :
    ∑ k ∈ Finset.range n, (k : ℚ) ^ 2 = (n : ℚ) ^ 3 / 3 - (n : ℚ) ^ 2 / 2 + (n : ℚ) / 6 := by
  kit_sum n

-- cases
/--
info: Sage-free replacement: 
  [apply] decide
-/
#guard_msgs in
example : ∀ x : Fin 4, x * x ≠ 2 := by kit_decide

/-! ## Replay -/

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
