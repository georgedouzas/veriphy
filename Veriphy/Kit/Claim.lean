/-
Claims as problems: a theorem or a definition of type `Prop`, its universal binders opened as locals and its body as
the goal, for `sage_test`; and the dependence of a proof on a claim, through this module's declarations.
-/
import Veriphy.Kit.Problem
import Veriphy.Kit.Levels

namespace Veriphy

open Lean Elab Meta Term Tactic

/-- The problem of a claim: its body as the goal with its universal binders as locals, and the binders listed by name
and type under `universal`. -/
def claimProblem (name : Name) : TermElabM (Json × Nat) := do
  let statement ← instantiateMVars (← claimStatement name)
  forallTelescope statement fun xs body => do
    let goal ← mkFreshExprMVar body
    let binders ← xs.mapM fun x => do
      return Json.mkObj [("name", Json.str (toString (← x.fvarId!.getUserName))),
        ("type", Json.str (toString (← ppExpr (← inferType x))))]
    let out ← IO.mkRef Json.null
    discard <| Tactic.run goal.mvarId! do
      out.set (← withLenientProblem fun p => p.toJson)
    return ((← out.get).setObjVal! "universal" (Json.arr binders), xs.size)

/-- The chain of this module's declarations through which `e` depends on `target`, or `none`. Imported declarations
are not entered: the claim under test is in this module. -/
partial def dependence (target : Name) (e : Expr) : MetaM (Option (List Name)) := do
  let env ← getEnv
  let rec visit (frontier : List (Name × List Name)) (seen : NameSet) : Option (List Name) :=
    match frontier with
    | [] => none
    | (c, path) :: rest =>
      if c == target then some (path.reverse ++ [c])
      else if seen.contains c || (env.getModuleIdxFor? c).isSome then visit rest (seen.insert c)
      else
        let next := match env.find? c with
          | some info => (info.type.getUsedConstants ++ (info.value?.map Expr.getUsedConstants).getD #[]).toList
          | none => []
        visit (rest ++ next.map (·, c :: path)) (seen.insert c)
  return visit (e.getUsedConstants.toList.map (·, [])) {}

end Veriphy
