/-
`sage_farkas`: linear arithmetic by certificate. The linear hypotheses in context (`=`, `≤`, `<`, `≥`, `>`
over an ordered field) are sent to Sage, which finds Farkas multipliers by an exact rational linear program;
Lean checks a single `linear_combination`. A goal `a ≤ b` or `a < b` is first negated. This is `linarith`
with the certificate search moved to Sage: useful when the system is large (e.g. anomaly-cancellation
conditions with many representations), and the emitted proof is Sage-free.
-/
import Veriphy.Kit

namespace Veriphy

open Lean Elab Tactic Meta

/-- `sage_farkas` — close `False`, `a ≤ b` or `a < b` from linear hypotheses via a Sage-found Farkas
certificate checked by `linear_combination`. Emits a Sage-free `Try this:`. -/
elab (name := sageFarkas) "sage_farkas" : tactic => do
  let h ← withMainContext (freshIdent `hfarkas)
  let negating := !(← instantiateMVars (← getMainTarget)).isConstOf ``False
  let o : ExtractOpts := { tac := "sage_farkas", goalRels := #[.le, .lt], allowFalse := true,
                           hypRels := #[.eq, .le, .lt], negateGoalAs := h.getId, needHyps := true }
  let (α, combo, cert) ← withProblem o fun p => do
    let cert ← Kit.run "farkas"
      (Bridge.farkas (p.hyps.toList.map (·.poly)) (p.hyps.toList.map (·.rel.tag)) p.vars)
    let weights := cert.multipliers.toArray.map Bridge.Term.const
    let combo ← weightedSum #[] (weights.zip (← p.hyps.mapM (·.ref)))
    return (← PrettyPrinter.delab (p.carrier.getD (mkConst ``Rat)), combo, cert)
  let pre ← if negating then Checker.negateGoal h else pure #[]
  closeAndEmit (← Checker.refute pre α cert.kappa cert.strict combo)

end Veriphy
