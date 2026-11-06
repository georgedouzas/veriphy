/-
`#veriphy_translate t`: what Veriphy's symbolic translation makes of a term, without Sage — its Sage form, the
atoms it needed and the domain conditions it imposes, under the tables in force (core, active packs, project).
-/
import Veriphy.Kit.Packs
import Veriphy.Kit.Symbolic

namespace Veriphy

open Lean Elab Command Meta

/-- The report for one term: Sage form, atoms (with types), conditions. -/
def inspectTerm (e : Expr) : MetaM String := do
  let (project, loadProblems) ← projectTables (veriphy.translationsDir.get (← getOptions))
  let (tables, resolveProblems) ← activeTables project
  let problems := loadProblems ++ resolveProblems
  let (s, st) ← (exprToSym e).run { atoms := #[], tables }
  let atoms ← st.atoms.toList.mapIdxM fun i a => return s!"  x{i} := {← ppExpr a} : {← atomType a}"
  let conds ← st.conditions.toList.mapM fun c => return s!"  {← ppExpr (← c.prop)}"
  return "\n".intercalate ([s!"sage: {s.toSage}", "atoms:"] ++ atoms ++ ["conditions:"] ++ conds ++
    problems.toList.map ("problem: " ++ ·))

/-- `#veriphy_translate t` — print the symbolic translation of the term `t`. -/
syntax (name := veriphyTranslate) "#veriphy_translate " term : command

elab_rules : command
  | `(#veriphy_translate $t) => runTermElabM fun _ => do
    let e ← instantiateMVars (← Term.elabTerm t none)
    Term.synthesizeSyntheticMVarsNoPostponing
    logInfo (← inspectTerm (← instantiateMVars e))

end Veriphy
