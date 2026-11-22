/-
`#veriphy translate t`: what Veriphy's symbolic translation makes of a term, without Sage — its Sage form, the
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

/-- `#veriphy translate t`: how the term `t` reaches Sage, its atoms and its conditions. -/
syntax (name := veriphyTranslateCommand) "#veriphy " &"translate " term : command

elab_rules : command
  | `(#veriphy translate $t) => runTermElabM fun _ => do
    let e ← instantiateMVars (← Term.elabTerm t none)
    Term.synthesizeSyntheticMVarsNoPostponing
    logInfo (← inspectTerm (← instantiateMVars e))

end Veriphy
