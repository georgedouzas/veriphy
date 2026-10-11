/-
Checker families: the fixed set of proof shapes certificate tactics close goals with.

  identity    `refine Eq.trans (show lhs = F by ring1) ?_`  or  `linear_combination Σ cᵢ * hᵢ`
  inequality  `linear_combination Σ wᵢ * hᵢ + Σ cⱼ * sq_nonneg qⱼ` (positivity side conditions),
              or refute: `have hκ : κ ≤ 0 := by linear_combination …; norm_num at hκ`
  witness     `exact ⟨v₁, …, vₙ, by norm_num⟩`
  sum         induction on `n`, both cases by `push_cast; ring1`
  cases       `decide`

Each family's `Checker.*` builder only *builds* the proof; `closeAndEmit` runs exactly that syntax (it is the
check — "run what you print"), replays it when `veriphy.checkReplay` is set, and emits it
once as the `Sage-free replacement:`. Only mathlib checkers close goals.
-/
import Mathlib.Tactic.LinearCombination
import Mathlib.Tactic.NormNum
import Mathlib.Tactic.Positivity
import Mathlib.Tactic.Ring
import Mathlib.Algebra.BigOperators.Group.Finset.Basic
import Veriphy.Kit.Build
import Veriphy.Kit.Replay

namespace Veriphy

open Lean Elab Tactic Meta

/-- The checker families (closed set; `sage_certify` exposes the first three). -/
inductive Family | identity | inequality | witness | sum | cases
  deriving BEq, Repr, Inhabited

/-- Run `proof` on the main goal, replay it if `veriphy.checkReplay` is set, and emit it as the single
`Sage-free replacement:` for the whole current tactic (`getRef`, so applying it also replaces the
tactic's arguments). On failure the state is restored and nothing is emitted. -/
def closeAndEmit (proof : TSyntax `tactic) : TacticM Unit := do
  let s₀ ← saveState
  let errors := fun (log : MessageLog) => log.reportedPlusUnreported.foldl
    (fun n m => if m.severity == .error then n + 1 else n) 0
  let before := errors (← Core.getMessageLog)
  try
    -- no error recovery: a checker failing inside a nested `by` must fail the tactic, not be logged
    Term.withoutErrToSorry <| withoutRecover <| evalTactic proof
    if errors (← Core.getMessageLog) > before then
      throwError "veriphy: the certificate check failed (see the errors above)"
  catch ex =>
    s₀.restore
    throw ex
  if veriphy.checkReplay.get (← getOptions) then
    replay s₀ proof (← getUnsolvedGoals)
  Lean.Meta.Tactic.TryThis.addSuggestion (← getRef) proof (header := "Sage-free replacement: ")

namespace Checker

/-! ## identity -/

/-- `lhs = rhs` ↦ `F = rhs`, certified `lhs = F` by `ring1`; leaves the residual goal. -/
def rewriteBy (lhs F : TSyntax `term) : TacticM (TSyntax `tactic) := do
  let trans := mkIdent ``Eq.trans
  `(tactic| refine $trans (show $lhs = $F by ring1) ?_)

/-- Close an equality (or, over an ordered field, an inequality) by `linear_combination combo`. -/
def linearCombination (combo : TSyntax `term) : TacticM (TSyntax `tactic) :=
  `(tactic| linear_combination $combo:term)

/-! ## inequality -/

/-- `c * sq_nonneg (q)` proof terms for square certificates. -/
def squareTerm (q : TSyntax `term) : TacticM (TSyntax `term) := do
  `($(mkIdent ``sq_nonneg) ($q))

/-- `0 ≤ p` from an exact decomposition `p = Σ cᵢ * qᵢ²` (`sumStx` its right side): `positivity` on the
sum, `ring1` on the identity. -/
def squares (sumStx pStx : TSyntax `term) : TacticM (TSyntax `tactic) := do
  let leOf := mkIdent ``le_of_le_of_eq
  `(tactic| exact $leOf (by positivity) (show $sumStx = $pStx by ring1))

/-- The steps that turn a `≤`/`<` goal into `False` with its negation as hypothesis `h`
(`¬ a ≤ b` becomes `b < a`, `¬ a < b` becomes `b ≤ a`; `≥`/`>` are unfolded first). -/
def negateGoal (h : Ident) : TacticM (Array (TSyntax `tactic)) := do
  let (a, b, c, d) := (mkIdent ``not_le, mkIdent ``not_lt, mkIdent ``ge_iff_le, mkIdent ``gt_iff_lt)
  return #[← `(tactic| by_contra $h:ident),
           ← `(tactic| simp only [$a:ident, $b:ident, $c:ident, $d:ident] at $h:ident)]

/-- Refute: `pre` steps, then `have hκ : (κ : α) (<|≤) 0 := by linear_combination combo`, then
`norm_num at hκ` (a false numeral inequality closes the goal). -/
def refute (pre : Array (TSyntax `tactic)) (α : TSyntax `term) (kappa : String) (strict : Bool)
    (combo : TSyntax `term) : TacticM (TSyntax `tactic) := do
  let hk ← freshIdent `hfk
  let κ ← ratStx' kappa
  let have_ ← if strict then
      `(tactic| have $hk:ident : ($κ : $α) < 0 := by linear_combination $combo:term)
    else `(tactic| have $hk:ident : ($κ : $α) ≤ 0 := by linear_combination $combo:term)
  stepsStx (pre ++ #[have_, ← `(tactic| norm_num at $hk:ident)])

/-! ## witness -/

/-- `exact ⟨v₁, …, vₙ, by norm_num⟩` for an `∃` goal with `binders` binders. -/
def witness (values : List String) (binders : Nat) : TacticM (TSyntax `tactic) := do
  let w ← witnessStx values binders (← `(by norm_num))
  `(tactic| exact $w)

/-! ## sum -/

/-- `∑ k ∈ Finset.range n, f k = F n` by induction on `n`: both cases by `push_cast` and `ring1`. -/
def sumInduction (n : Ident) : TacticM (TSyntax `tactic) := do
  let (zero, succ) := (mkIdent ``Finset.sum_range_zero, mkIdent ``Finset.sum_range_succ)
  let (m, ih) := (mkIdent `n, mkIdent `ih)
  let (z, sc) := (mkIdent `zero, mkIdent `succ)  -- constructor names, spliced so they print unhygienic
  `(tactic|
    induction $n:ident with
    | $z:ident => rw [$zero:ident]; (try push_cast); ring1
    | $sc:ident $m:ident $ih:ident => rw [$succ:ident, $ih:ident]; (try push_cast); ring1)

/-! ## cases -/

/-- A decidable goal over a finite domain, by `decide`. -/
def cases : TacticM (TSyntax `tactic) := `(tactic| decide)

end Checker

end Veriphy
