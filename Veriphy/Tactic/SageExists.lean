/-
`sage_exists`: rational witnesses. On a goal `∃ x₁ … xₙ, P` where `P` is a conjunction of polynomial
equations, linear inequalities and disequalities with no other free variables, Sage finds a rational point and
Lean checks it with `norm_num`. Typical uses: null vectors and eigenvectors (`A v = λ B v`, `v ≠ 0`),
explicit counterexamples, feasible charge assignments.
-/
import Veriphy.Kit

namespace Veriphy

open Lean Elab Tactic Meta

/-- `sage_exists` — close `∃ x₁ … xₙ, P` with a Sage-found rational witness checked by `norm_num`. -/
elab (name := sageExists) "sage_exists" : tactic => do
  let (point, n) ← withProblem { tac := "sage_exists", allowExists := true } fun p => do
    let .exists_ binders body := p.goal | unreachable!
    let pick (r : Rel) := (body.filter (·.rel == r)).toList.map (·.poly)
    let point ← Kit.run "exists" (Bridge.exists_ p.vars (pick .eq) (pick .le) (pick .lt) (pick .ne))
    return (point, binders.size)
  closeAndEmit (← Checker.witness point n)

end Veriphy
