/-
`sage_farkas`: linear arithmetic by certificate. The linear hypotheses in context (`=`, `≤`, `<`, `≥`, `>`
over an ordered field) are sent to Sage, which finds Farkas multipliers by an exact rational linear program;
Lean checks a single `linear_combination`. A goal `a ≤ b` or `a < b` is first negated. This is `linarith`
with the certificate search moved to Sage: useful when the system is large (e.g. anomaly-cancellation
conditions with many representations), and the emitted proof is Sage-free.
-/
import Mathlib.Tactic.LinearCombination
import Mathlib.Tactic.NormNum
import Veriphy.Translate

namespace Veriphy

open Lean Elab Tactic Meta Bridge

private inductive Rel | eq | le | lt

/-- `(lhs, rhs, relation)` meaning `lhs - rhs (rel) 0`, for a hypothesis type. -/
private def relOf? (t : Expr) : Option (Expr × Expr × Expr × Rel) :=
  match t.getAppFnArgs with
  | (``Eq, #[α, a, b]) => some (α, a, b, .eq)
  | (``LE.le, #[α, _, a, b]) => some (α, a, b, .le)
  | (``LT.lt, #[α, _, a, b]) => some (α, a, b, .lt)
  | (``GE.ge, #[α, _, a, b]) => some (α, b, a, .le)
  | (``GT.gt, #[α, _, a, b]) => some (α, b, a, .lt)
  | _ => none

/-- `sage_farkas` — close `False`, `a ≤ b` or `a < b` from linear hypotheses via a Sage-found Farkas
certificate checked by `linear_combination`. Emits a Sage-free `Try this:`. -/
elab (name := sageFarkas) ref:"sage_farkas" : tactic => do
  let mut steps : Array (TSyntax `tactic) := #[]
  let tgt ← instantiateMVars (← (← getMainGoal).getType)
  unless tgt.isConstOf ``False do
    match relOf? tgt with
    | some (_, _, _, r@(.le)) | some (_, _, _, r@(.lt)) =>
      let hn := mkIdent `hfarkas
      let s1 ← `(tactic| by_contra $hn:ident)
      let lem := mkIdent (match r with | .lt => ``not_lt | _ => ``not_le)
      let s2 ← `(tactic| simp only [$lem:ident] at $hn:ident)
      evalTactic s1; evalTactic s2
      steps := steps.push s1 |>.push s2
    | _ => throwError "sage_farkas: goal must be `False`, `a ≤ b` or `a < b`, got{indentExpr tgt}"
  let more ← withMainContext do
    let atomsRef ← IO.mkRef (#[] : Array Expr)
    let runTr (e : Expr) : MetaM String := do
      let (s, atoms) ← (exprToSage e).run (← atomsRef.get)
      atomsRef.set atoms
      return s
    let mut ty? : Option Expr := none
    let mut ids : Array Ident := #[]
    let mut polys : List String := []
    let mut rels : List String := []
    for decl in ← getLCtx do
      if decl.isImplementationDetail || decl.userName.hasMacroScopes then continue
      let some (α, a, b, r) := relOf? (← instantiateMVars decl.type) | continue
      match ty? with
      | none => ty? := some α
      | some β => unless ← withReducible (isDefEq α β) do continue
      let saved ← atomsRef.get
      try
        let sa ← runTr a
        let sb ← runTr b
        ids := ids.push (mkIdent decl.userName)
        polys := polys ++ [s!"({sa}) - ({sb})"]
        rels := rels ++ [match r with | .eq => "eq" | .le => "le" | .lt => "lt"]
      catch _ => atomsRef.set saved
    let some α := ty? | throwError "sage_farkas: no linear hypotheses in context"
    let atoms ← atomsRef.get
    if atoms.isEmpty then throwError "sage_farkas: no variables in the hypotheses"
    let cert ← Bridge.farkas polys rels (sageVarNames atoms)
    let mut pieces : Array (TSyntax `term) := #[]
    for (m, h) in cert.multipliers.toArray.zip ids do
      if m == "0" then continue
      pieces := pieces.push (← `(($(← ratStx' m)) * $h))
    if pieces.isEmpty then throwError "sage_farkas: empty certificate"
    let combo ← pieces[1:].foldlM (fun acc p => `($acc + $p)) pieces[0]!
    let αStx ← PrettyPrinter.delab α
    let κ ← ratStx' cert.kappa
    let hk := mkIdent `hfk
    let s3 ← if cert.strict then `(tactic| have $hk:ident : ($κ : $αStx) < 0 := by linear_combination $combo:term)
             else `(tactic| have $hk:ident : ($κ : $αStx) ≤ 0 := by linear_combination $combo:term)
    let s4 ← `(tactic| norm_num at $hk:ident)
    evalTactic s3; evalTactic s4
    pure #[s3, s4]
  steps := steps ++ more
  let proof ← `(tactic| ($[$steps]*))
  Lean.Meta.Tactic.TryThis.addSuggestion ref proof (header := "Sage-free replacement: ")

end Veriphy
