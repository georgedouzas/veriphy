/-
`sage_lincomb`: local polyrith. On a goal `lhs = rhs` with hypothesis
equalities `hᵢ : aᵢ = bᵢ`, Sage computes Gröbner-basis cofactors `cᵢ` with
`lhs - rhs = Σ cᵢ * (aᵢ - bᵢ)` (`ideal.lift`); Lean verifies the whole
combination with `linear_combination` (which closes by `ring1`). This is
mathlib's `polyrith` idea with a local daemon instead of a web service, and a
Sage-free `Try this:` output.
-/
import Mathlib.Tactic.LinearCombination
import Veriphy.Translate

namespace Veriphy

open Lean Elab Tactic Meta Bridge

/-- `sage_lincomb` — prove a polynomial equality goal from the polynomial
equality hypotheses in context, via a Sage ideal-membership certificate
checked by `linear_combination`. -/
elab (name := sageLincomb) ref:"sage_lincomb" : tactic => withMainContext do
  let goal ← getMainGoal
  let tgt ← instantiateMVars (← goal.getType)
  let some (α, lhs, rhs) := tgt.eq?
    | throwError "sage_lincomb: goal must be an equality, got{indentExpr tgt}"
  -- shared atom table across goal and hypotheses
  let atomsRef ← IO.mkRef (#[] : Array Expr)
  let runTr (e : Expr) : MetaM String := do
    let (s, atoms) ← (exprToSage e).run (← atomsRef.get)
    atomsRef.set atoms
    return s
  let targetStr ← do
    let l ← runTr lhs
    let r ← runTr rhs
    pure s!"({l}) - ({r})"
  -- usable hypotheses: equalities in the same ring that translate
  let mut hypIds : Array Ident := #[]
  let mut hypStrs : List String := []
  for decl in ← getLCtx do
    if decl.isImplementationDetail then continue
    let some (β, a, b) := (← instantiateMVars decl.type).eq? | continue
    unless ← withReducible (isDefEq α β) do continue
    let saved ← atomsRef.get
    try
      let sa ← runTr a
      let sb ← runTr b
      hypIds := hypIds.push (mkIdent decl.userName)
      hypStrs := hypStrs ++ [s!"({sa}) - ({sb})"]
    catch _ =>
      atomsRef.set saved  -- untranslatable hypothesis: skip it
  if hypIds.isEmpty then
    throwError "sage_lincomb: no usable equality hypotheses in context"
  let atoms ← atomsRef.get
  let cofactors ← Bridge.lincomb targetStr hypStrs (sageVarNames atoms)
  unless cofactors.length == hypIds.size do
    throwError "sage_lincomb: certificate shape mismatch"
  -- build Σ cofᵢ * hᵢ, dropping zero cofactors
  let atomStx ← atoms.mapM fun a => PrettyPrinter.delab a
  let mut pieces : Array (TSyntax `term) := #[]
  for (cof, h) in cofactors.toArray.zip hypIds do
    if cof.isEmpty then continue
    let c ← polyStx atomStx cof
    pieces := pieces.push (← `(($c) * $h))
  if pieces.isEmpty then
    throwError "sage_lincomb: empty certificate (is the goal provable by ring alone?)"
  let combo ← pieces[1:].foldlM (fun acc p => `($acc + $p)) pieces[0]!
  let proof ← `(tactic| linear_combination $combo:term)
  evalTactic proof  -- linear_combination's ring1 check is the certification
  Lean.Meta.Tactic.TryThis.addSuggestion ref proof
    (header := "Sage-free replacement: ")

end Veriphy
