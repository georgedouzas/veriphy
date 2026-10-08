/-
`sage_witness`: close `∃ x, p x = q x` (polynomial, one bound variable, no
other parameters) by asking Sage for a rational root. The root is only a
*witness* — `norm_num` checks it in-kernel, so Sage stays untrusted. The
classic asymmetry: root-finding is hard, root-checking is arithmetic.
-/
import Mathlib.Tactic.NormNum
import Veriphy.Translate

namespace Veriphy

open Lean Elab Tactic Meta Bridge

/-- `sage_witness` — on a goal `∃ x, p x = q x` over a field with `p, q`
polynomial in `x` alone, find a rational root via Sage and close the goal
with the checked witness. Emits a Sage-free `Try this:`. -/
elab (name := sageWitness) ref:"sage_witness" : tactic => withMainContext do
  let goal ← getMainGoal
  let tgt ← instantiateMVars (← goal.getType)
  let (polyStr) ← do
    match tgt.getAppFnArgs with
    | (``Exists, #[_, pred]) =>
      lambdaTelescope pred fun xs body => do
        let #[x] := xs
          | throwError "sage_witness: expected a single bound variable"
        let some (_, l, r) := body.eq?
          | throwError "sage_witness: body must be an equality, got{indentExpr body}"
        -- seed the atom table with the bound variable so it becomes x0
        let (ls, atoms) ← (exprToSage l).run #[x]
        let (rs, atoms) ← (exprToSage r).run atoms
        unless atoms.size == 1 do
          throwError "sage_witness: only the bound variable may appear \
            (found {atoms.size - 1} extra atom(s))"
        pure s!"({ls}) - ({rs})"
    | _ => throwError "sage_witness: goal must be an existential, got{indentExpr tgt}"
  let roots ← Bridge.roots polyStr "x0"
  let some root := roots.head?
    | throwError "sage_witness: no rational root found"
  let c ← ratStx' root
  let proof ← `(tactic| exact ⟨$c, by norm_num⟩)
  evalTactic proof  -- norm_num's witness check is the certification
  Lean.Meta.Tactic.TryThis.addSuggestion ref proof
    (header := "Sage-free replacement: ")

end Veriphy
