/-
`sage_sos`: close goals `0 ≤ p` / `p ≥ 0` via an exact sum-of-squares
certificate. Sage decomposes `p = Σ cᵢ * qᵢ²` (cᵢ ≥ 0 rationals); Lean
verifies by `ring1` (the identity) and `positivity` (nonnegativity of the
sum). Sage is untrusted: a bogus decomposition fails the `ring1` check.

Current daemon coverage: polynomials whose odd-multiplicity irreducible
factors are constants or single-variable positive-definite quadratics (this
includes all even-power cases like perfect squares). Unsupported shapes fail
with the daemon's explanation — that failure is ledger data, not a bug.

`sage_sos [q₁, …, qₖ]` supplies candidate squares: Sage finds exact rationals
`c₀, cᵢ ≥ 0` with `p = c₀ + Σ cᵢ qᵢ²` (an exact rational LP), and the same
`positivity` + `ring1` check closes the goal. Useful when the squares are known
from structure (e.g. field strengths) but `p` does not factor.
-/
import Veriphy.Kit

namespace Veriphy

open Lean Elab Tactic Meta

private def squareStx (atoms : Array (TSyntax `term)) (s : Bridge.Square) :
    TermElabM (TSyntax `term) := do
  let q ← polyStx atoms s.terms
  let sq ← `(($q) ^ 2)
  let some (n, d) := parseRat s.coeff
    | throwError "sage_sos: bad coefficient in certificate: {s.coeff}"
  if n == 1 && d == 1 then pure sq
  else `($(← ratStx n d) * $sq)

/-- Core of `sage_sos`, with optional hinted squares. -/
def sageSOSCore (hintStx : Array (TSyntax `term)) : TacticM Unit := withMainContext do
  -- `0 ≤ p` and `p ≥ 0` both normalize to `0 - p ≤ 0`; the hints share the goal's atom table
  let tgt ← instantiateMVars (← getMainTarget)
  let some (_, z, p, .le) := relOf? tgt
    | throwError "sage_sos: goal must be `0 ≤ p` or `p ≥ 0`, got{indentExpr tgt}"
  unless natLit? z == some 0 do
    throwError "sage_sos: goal must be `0 ≤ p` or `p ≥ 0`, got{indentExpr tgt}"
  let pTy ← inferType p
  let hints ← hintStx.mapM fun h => Term.elabTermEnsuringType h pTy
  let (sumStx, pStx) ← withProblem { tac := "sage_sos", goalRels := #[.le], extras := #[p] ++ hints }
    fun prob => do
      let squares ← Kit.run "sos" (Bridge.sos prob.extras[0]! prob.vars {} prob.extras[1:].toList)
      let atoms ← prob.atomStx
      let sqStx ← squares.toArray.mapM (squareStx atoms)
      let sumStx ← if sqStx.isEmpty then `((0 : _)) else sqStx[1:].foldlM (fun acc s => `($acc + $s)) sqStx[0]!
      return (sumStx, ← PrettyPrinter.delab p)
  -- inequality family, squares form: `positivity` on the sum, `ring1` on the identity
  closeAndEmit (← Checker.squares sumStx pStx)

/-- `sage_sos` — close a goal `0 ≤ p` or `p ≥ 0` via a Sage sum-of-squares certificate (see the module doc). -/
syntax (name := sageSOS) "sage_sos" (" [" term,* "]")? : tactic

elab_rules : tactic
  | `(tactic| sage_sos) => sageSOSCore #[]
  | `(tactic| sage_sos [$hs,*]) => sageSOSCore hs.getElems

end Veriphy
