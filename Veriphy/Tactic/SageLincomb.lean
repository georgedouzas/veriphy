/-
`sage_lincomb`: local polyrith. On a goal `lhs = rhs` with hypothesis
equalities `hᵢ : aᵢ = bᵢ`, Sage computes Gröbner-basis cofactors `cᵢ` with
`lhs - rhs = Σ cᵢ * (aᵢ - bᵢ)` (`ideal.lift`); Lean verifies the whole
combination with `linear_combination` (which closes by `ring1`). This is
mathlib's `polyrith` idea with a local daemon instead of a web service, and a
Sage-free `Try this:` output.
-/
import Veriphy.Kit

namespace Veriphy

open Lean Elab Tactic Meta

/-- `sage_lincomb` — prove a polynomial equality goal from the polynomial
equality hypotheses in context, via a Sage ideal-membership certificate
checked by `linear_combination`. -/
elab (name := sageLincomb) "sage_lincomb" : tactic => do
  let combo ← withProblem { tac := "sage_lincomb", goalRels := #[.eq], hypRels := #[.eq], needHyps := true }
    fun p => do
      let .rel g := p.goal | unreachable!
      let cofs ← Kit.run "lincomb" (Bridge.lincomb g.poly (p.hyps.toList.map (·.poly)) p.vars)
      unless cofs.length == p.hyps.size do throwError "sage_lincomb: certificate shape mismatch"
      weightedSum (← p.atomStx) (cofs.toArray.zip (← p.hyps.mapM (·.ref)))
  closeAndEmit (← Checker.linearCombination combo)

end Veriphy
