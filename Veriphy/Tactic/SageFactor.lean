/-
`sage_factor`: on a goal `lhs = rhs`, factor `lhs` through the Sage daemon,
certify `lhs = factored` in-kernel with `ring1` (Sage untrusted, identity
family), and leave the goal `factored = rhs`. Emits a `Try this:` replacement that checks without
Sage. Also provides the `#sage_factor` diagnostic command.
-/
import Veriphy.Kit

namespace Veriphy

open Lean Elab Tactic Meta Bridge

private def factorStx (atoms : Array (TSyntax `term)) (f : Bridge.Factor) :
    TermElabM (TSyntax `term) := do
  let sum ← polyStx atoms f.terms
  if f.mult == 1 then `(($sum))
  else
    let mlit : TSyntax `num := Syntax.mkNumLit (toString f.mult)
    `(($sum) ^ $mlit)

private def certStx (atoms : Array (TSyntax `term)) (cert : FactorCert) :
    TermElabM (TSyntax `term) := do
  let fs ← cert.factors.toArray.mapM (factorStx atoms)
  let some (n, d) := parseRat cert.unit
    | throwError "sage_factor: bad unit in certificate: {cert.unit}"
  if fs.isEmpty then
    ratStx n d
  else
    let prod ← fs[1:].foldlM (fun acc f => `($acc * $f)) fs[0]!
    if n == 1 && d == 1 then pure prod
    else if n == -1 && d == 1 then `(-$prod)
    else `($(← ratStx n d) * $prod)

/-- `sage_factor` — on a goal `lhs = rhs`, replace it with `factored = rhs`
where `factored` is Sage's factorization of `lhs`, certified in-kernel by
`ring1`. Emits a `Try this:` replacement that checks without Sage. -/
elab (name := sageFactor) "sage_factor" : tactic => do
  let (lhs, factored) ← withProblem { tac := "sage_factor", goalRels := #[.eq], lhsOnly := true } fun p => do
    let .rel g := p.goal | unreachable!
    let cert ← Kit.run "factor" (Bridge.factor g.poly p.vars)
    return (← PrettyPrinter.delab g.lhs, ← certStx (← p.atomStx) cert)
  closeAndEmit (← Checker.rewriteBy lhs factored)

/-! ## Diagnostic command -/

private def termToString (vars : List String) (t : Bridge.Term) : String :=
  let monos := (vars.zip t.exps).filterMap fun (v, e) =>
    if e = 0 then none else if e = 1 then some v else some s!"{v}^{e}"
  String.intercalate "*" (t.coeff :: monos)

private def factorToString (vars : List String) (f : Bridge.Factor) : String :=
  let body := String.intercalate " + " (f.terms.map (termToString vars))
  if f.mult = 1 then s!"({body})" else s!"({body})^{f.mult}"

/-- `#sage_factor "x^4 - 1" "x"` — show the daemon's factorization certificate
over `ℚ[vars]` (variables as trailing string literals). -/
elab "#sage_factor " poly:str vars:str+ : command => do
  let varsList := vars.toList.map (·.getString)
  let cert ← Bridge.factor poly.getString varsList
  let pretty := String.intercalate " * " (cert.factors.map (factorToString varsList))
  logInfo s!"certificate: {cert.unit} * {pretty}\n(check obligation: {poly.getString} = the above, by ring)"

end Veriphy
