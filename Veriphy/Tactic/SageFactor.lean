/-
`sage_factor`: the first Veriphy certificate tactic.

Certificate shape: Sage returns `unit * ∏ fᵢ ^ mᵢ` as structured term lists
(Bridge.FactorCert). The checker rebuilds that product as a Lean expression and
closes `lhs = product` with `ring` — Sage's answer is verified, never trusted.
Per the Veriphy design rule, the tactic then emits a `Try this:` replacement
(`rw [show lhs = ... from by ring]` / `linear_combination`-style) so committed
proofs check without Sage installed.

STATUS: scaffold. Working here: `#sage_factor` command that calls the daemon
and reports the certified factorization shape. TODO (first real milestone):
  1. term-list → `Expr` reconstruction over `ℚ`/commutative rings
  2. close the equality goal via `Mathlib.Tactic.Ring`
  3. `Try this:` suggestion via `Lean.Meta.Tactic.TryThis`
-/
import Veriphy.Bridge

namespace Veriphy

open Lean Elab Command Bridge

private def termToString (vars : List String) (t : Term) : String :=
  let monos := (vars.zip t.exps).filterMap fun (v, e) =>
    if e = 0 then none else if e = 1 then some v else some s!"{v}^{e}"
  String.intercalate "*" (t.coeff :: monos)

private def factorToString (vars : List String) (f : Factor) : String :=
  let body := String.intercalate " + " (f.terms.map (termToString vars))
  if f.mult = 1 then s!"({body})" else s!"({body})^{f.mult}"

/-- `#sage_factor "x^4 - 1" ["x"]` — ask the daemon for a factorization
certificate and display it. Diagnostic command; the goal-closing tactic
version is the project's first milestone. -/
elab "#sage_factor " poly:str vars:term : command => do
  let varsList ← liftTermElabM do
    let e ← Term.elabTerm vars (some (.app (.const ``List []) (.const ``String [])))
    unsafe Meta.evalExpr (List String) (.app (.const ``List []) (.const ``String [])) e
  let cert ← Bridge.factor poly.getString varsList
  let pretty := String.intercalate " * " (cert.factors.map (factorToString varsList))
  logInfo s!"certificate: {cert.unit} * {pretty}\n(check obligation: {poly.getString} = the above, by ring)"

end Veriphy
