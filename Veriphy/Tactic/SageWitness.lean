/-
`sage_witness`: close `∃ x, p x = q x` (polynomial, one bound variable, no
other parameters) by asking Sage for a rational root. The root is only a
*witness* — `norm_num` checks it in-kernel, so Sage stays untrusted. The
classic asymmetry: root-finding is hard, root-checking is arithmetic.
-/
import Veriphy.Kit

namespace Veriphy

open Lean Elab Tactic Meta

/-- `sage_witness` — on a goal `∃ x, p x = q x` over a field with `p, q`
polynomial in `x` alone, find a rational root via Sage and close the goal
with the checked witness. Emits a Sage-free `Try this:`. -/
elab (name := sageWitness) "sage_witness" : tactic => do
  let root ← withProblem { tac := "sage_witness", allowExists := true } fun p => do
    let .exists_ binders body := p.goal | unreachable!
    unless binders.size == 1 do throwError "sage_witness: expected a single bound variable"
    let #[c] := body | throwError "sage_witness: body must be a single equality"
    unless c.rel == .eq do throwError "sage_witness: body must be an equality"
    let some root := (← Kit.run "roots" (Bridge.roots c.poly "x0")).head?
      | throwError "sage_witness: no rational root found"
    return root
  closeAndEmit (← Checker.witness [root] 1)

end Veriphy
