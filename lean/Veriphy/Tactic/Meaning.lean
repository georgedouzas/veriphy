/-
`#veriphy meaning c`: does the statement of the claim `c` say what it was meant to? The kernel cannot answer that, so
the command tests the statement: Sage draws seeded values for its universal binders, keeps those that satisfy the
hypotheses and the domain conditions of the functions it uses, and evaluates the conclusion at each, exactly or in
interval arithmetic of 128 bits. An equation is first tried symbolically.

The outcome is `agrees` (at so many values, or symbolically), `counterexample` (with the values and both sides) or
`undecided` (with the reason, such as the hypothesis that rejected most values). It is evidence, never a level: a
statement that agrees everywhere it was tried is not proved.

`#veriphy meaning c seed 3 values 20` sets the seed and how many values must agree, and
`#veriphy meaning c points "[{\"x\": \"pi\"}]"` evaluates at the given values instead of drawing them.
-/
import Veriphy.Kit
import Veriphy.Kit.Claim

namespace Veriphy

open Lean Elab Meta Term Command

register_option veriphy.meaning.json : Bool := {
  defValue := false
  descr := "Veriphy: `#veriphy meaning` also logs its whole result as JSON, for `python -m veriphy layers step meaning`"
}

/-- How many values must agree when `values` is not given. -/
def meaningDefaultValues : Nat := 10

/-- The problem of a claim for the meaning check: its body as the goal, its universal binders as locals, and every
hypothesis binder with no name that can be written (an arrow's) renamed `hyp₀ …`, so it serializes as a hypothesis;
`intros` lists every binder's name in order, for a proof that introduces them. -/
def meaningProblem (name : Name) : TermElabM Json := do
  let statement ← instantiateMVars (← claimStatement name)
  forallTelescope statement fun xs body => do
    let mut lctx ← getLCtx
    let mut hypotheses := 0
    for x in xs do
      let decl ← x.fvarId!.getDecl
      if (← isProp decl.type) && !nameable decl then
        lctx := lctx.setUserName x.fvarId! (Name.mkSimple s!"hyp{hypotheses}")
        hypotheses := hypotheses + 1
    withLCtx lctx (← getLocalInstances) do
      let mut binders := #[]
      for x in xs do
        let ty ← inferType x
        unless ← isProp ty do
          binders := binders.push <| Json.mkObj [("name", Json.str (toString (← x.fvarId!.getUserName))),
            ("type", Json.str (toString (← ppExpr ty)))]
      let goal ← mkFreshExprMVar body
      let out ← IO.mkRef Json.null
      discard <| Tactic.run goal.mvarId! do
        out.set (← withLenientProblem fun p => p.toJson)
      let intros ← xs.mapM fun x => return Json.str (toString (← x.fvarId!.getUserName))
      return ((← out.get).setObjVal! "universal" (Json.arr binders)).setObjVal! "intros" (Json.arr intros)

/-- The values of one point, as `x := 1, y := 1/2`. -/
private def showPoint (j : Json) : String :=
  match j with
  | .obj kvs => ", ".intercalate (kvs.toList.map fun (k, v) => s!"{k} := {v.getStr?.toOption.getD v.compress}")
  | _ => j.compress

/-- The one-line summary of a meaning check's result. -/
def meaningSummary (name : Name) (r : Json) : String :=
  let str (k : String) := (r.getObjValAs? String k).toOption.getD ""
  match str "outcome" with
  | "agrees" =>
    if str "method" == "symbolic" then s!"meaning: `{name}` agrees symbolically"
    else
      let n := (r.getObjValAs? Nat "agreed").toOption.getD 0
      let values := if n == 1 then "1 value" else s!"{n} values"
      let at_ := if (r.getObjValAs? Bool "given").toOption.getD false then s!"the {values} given"
        else s!"{values} (seed {(r.getObjValAs? Nat "seed").toOption.getD 0})"
      s!"meaning: `{name}` agrees at {at_}" ++ (if str "note" == "" then "" else s!"; {str "note"}")
  | "counterexample" =>
    let c := (r.getObjVal? "counterexample").toOption.getD Json.null
    let side (k : String) := (c.getObjValAs? String k).toOption.getD "?"
    s!"meaning: `{name}` fails at {showPoint ((c.getObjVal? "values").toOption.getD Json.null)}: \
      the left side is {side "lhs"} and the right side {side "rhs"}"
  | other => s!"meaning: `{name}` is {other}: {str "reason"}"

/-- Run the meaning check on the claim `target`. -/
def meaningCore (target : Ident) (seed values : Nat) (points : Option String) : CommandElabM Unit := do
  let (name, result) ← liftTermElabM do
    let name ← realizeGlobalConstNoOverloadWithInfo target
    let problem ← meaningProblem name
    let points ← match points with
      | none => pure Json.null
      | some text => match Json.parse text with
        | .ok j => pure j
        | .error e => throwError "#veriphy meaning: the points are not JSON ({e}): {text}"
    let result ← Kit.run "meaning" (Bridge.meaning problem seed values points)
    return (name, result)
  logInfo (meaningSummary name result)
  if veriphy.meaning.json.get (← getOptions) then
    logInfo m!"veriphy-meaning {result.compress}"

/-- `#veriphy serialize c`: log the problem of the claim `c` for the meaning check, with its statement, as
`veriphy-problem <json>`; the `lean.serialize` primitive reads it. -/
syntax (name := veriphySerialize) "#veriphy " &"serialize " ident : command

elab_rules : command
  | `(#veriphy serialize $c:ident) => do
    let json ← liftTermElabM do
      let name ← realizeGlobalConstNoOverloadWithInfo c
      let problem ← meaningProblem name
      let statement := toString (← ppExpr (← instantiateMVars (← claimStatement name)))
      let kind := if (← getConstInfo name) matches .thmInfo _ then "theorem" else "definition"
      return Json.mkObj [("declaration", Json.str name.toString), ("kind", Json.str kind),
        ("statement", Json.str statement), ("problem", problem)]
    logInfo m!"veriphy-problem {json.compress}"

end Veriphy
