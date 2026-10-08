/-
`sage_sos`: close goals `0 ≤ p` / `p ≥ 0` via an exact sum-of-squares
certificate. Sage decomposes `p = Σ cᵢ * qᵢ²` (cᵢ ≥ 0 rationals); Lean
verifies by `ring1` (the identity) and `positivity` (nonnegativity of the
sum). Sage is untrusted: a bogus decomposition fails the `ring1` check.

Current daemon coverage: polynomials whose odd-multiplicity irreducible
factors are constants or single-variable positive-definite quadratics (this
includes all even-power cases like perfect squares). Unsupported shapes fail
with the daemon's explanation — that failure is ledger data, not a bug.
-/
import Mathlib.Tactic.Positivity
import Veriphy.Translate

namespace Veriphy

open Lean Elab Tactic Meta Bridge

private def squareStx (atoms : Array (TSyntax `term)) (s : Bridge.Square) :
    TermElabM (TSyntax `term) := do
  let q ← polyStx atoms s.terms
  let sq ← `(($q) ^ 2)
  let some (n, d) := parseRat s.coeff
    | throwError "sage_sos: bad coefficient in certificate: {s.coeff}"
  if n == 1 && d == 1 then pure sq
  else `($(← ratStx n d) * $sq)

/-- `sage_sos` — close a goal `0 ≤ p` or `p ≥ 0` (`p` a polynomial over a
linear ordered field) via a Sage sum-of-squares certificate, verified
in-kernel by `ring1` + `positivity`. Emits a Sage-free `Try this:`. -/
elab (name := sageSOS) ref:"sage_sos" : tactic => withMainContext do
  let goal ← getMainGoal
  let tgt ← instantiateMVars (← goal.getType)
  let p ← do
    match tgt.getAppFnArgs with
    | (``LE.le, #[_, _, z, p]) =>
      unless natLit? z == some 0 do
        throwError "sage_sos: goal must be `0 ≤ p` or `p ≥ 0`, got{indentExpr tgt}"
      pure p
    | (``GE.ge, #[_, _, p, z]) =>
      unless natLit? z == some 0 do
        throwError "sage_sos: goal must be `0 ≤ p` or `p ≥ 0`, got{indentExpr tgt}"
      pure p
    | _ => throwError "sage_sos: goal must be `0 ≤ p` or `p ≥ 0`, got{indentExpr tgt}"
  let (polyStr, atoms) ← (exprToSage p).run #[]
  if atoms.isEmpty then
    throwError "sage_sos: no variables found in{indentExpr p}"
  let squares ← Bridge.sos polyStr (sageVarNames atoms)
  let atomStx ← atoms.mapM fun a => PrettyPrinter.delab a
  let sumStx : TSyntax `term ← liftM (m := TermElabM) do
    let sqStx ← squares.toArray.mapM (squareStx atomStx)
    if sqStx.isEmpty then `((0 : _)) else
      sqStx[1:].foldlM (fun acc s => `($acc + $s)) sqStx[0]!
  let pStx ← PrettyPrinter.delab p
  -- the whole proof is the (Sage-free) replacement; running it IS the check
  let leOf := mkIdent ``le_of_le_of_eq
  let proof ← `(tactic|
    exact $leOf (by positivity) (show $sumStx = $pStx by ring1))
  evalTactic proof
  Lean.Meta.Tactic.TryThis.addSuggestion ref proof
    (header := "Sage-free replacement: ")

end Veriphy
