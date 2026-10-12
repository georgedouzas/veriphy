/-
`sage_certify <family> "<sage script>"`: one-off certificates written by the agent.

The goal and context are extracted into the normalized problem every `sage_*`
tactic uses; the script runs in Sage with it pre-bound (`R`, generators `x0, x1, …`,
`hyps` as `Hyp(name, poly, rel)` meaning `poly rel 0`, `goal`, `binders`, `body`,
`atoms`) and assigns `certificate`:

  identity    {'cofactors': {hyp: poly}}                 goal `a = b`
  inequality  {'weights': {hyp: w}, 'squares': [(c, q)]}  goal `a ≤ b`, `a < b` or `False`
  witness     [v₁, …, vₙ]                                 goal `∃ x₁ … xₙ, …`

The certificate is untrusted: it is rebuilt with the kit's builders and closed by
the family's checker. The `Try this:` is the plain checker proof — the script never
reaches committed proofs.
-/
import Veriphy.Kit

namespace Veriphy

open Lean Elab Tactic Meta

declare_syntax_cat certifyFamily
syntax "identity" : certifyFamily
syntax "inequality" : certifyFamily
syntax "witness" : certifyFamily

private def familyOf : TSyntax `certifyFamily → TacticM Family
  | `(certifyFamily| identity) => pure .identity
  | `(certifyFamily| inequality) => pure .inequality
  | `(certifyFamily| witness) => pure .witness
  | _ => throwUnsupportedSyntax

private def opts (f : Family) : ExtractOpts :=
  match f with
  | .identity => { tac := "sage_certify identity", goalRels := #[.eq], hypRels := #[.eq] }
  | .inequality => { tac := "sage_certify inequality", goalRels := #[.le, .lt], allowFalse := true,
                     hypRels := #[.eq, .le, .lt] }
  | _ => { tac := "sage_certify witness", allowExists := true }

private def familyName : Family → String
  | .identity => "identity" | .inequality => "inequality" | _ => "witness"

/-- What the certificate rebuilds to, by family and goal. -/
private inductive Built
  | witness (point : List String) (binders : Nat)
  | direct (combo : TSyntax `term)
  | refute (α : TSyntax `term) (kappa : String) (strict : Bool) (combo : TSyntax `term)

/-- `sage_certify identity|inequality|witness "<script>"` — check an agent-written Sage certificate with
the family's checker (see the module doc). Emits the plain, Sage-free checker proof. -/
elab (name := sageCertify) "sage_certify " fam:certifyFamily script:str : tactic => do
  let f ← familyOf fam
  -- the goal shape is checked by extraction, before Sage is contacted
  let built ← withProblem (opts f) fun p => do
    let problem ← p.toJson
    let cert ← Kit.run "certify" (Bridge.certify problem (familyName f) script.getString)
    if let .exists_ binders _ := p.goal then
      return Built.witness cert.point binders.size
    let atoms ← p.atomStx
    let byName (n : String) : TermElabM (TSyntax `term) := do
      let some c := p.hyps.find? (·.src == some n.toName)
        | throwError "sage_certify: the certificate names unknown hypothesis '{n}'"
      c.ref
    let mut items := #[]
    for w in cert.weights do items := items.push (w.poly, ← byName w.name)
    for s in cert.squares do
      items := items.push (Bridge.Term.const s.coeff, ← `($(mkIdent ``sq_nonneg) ($(← polyStx atoms s.terms))))
    let combo ← weightedSum atoms items
    match p.goal, cert.kappa with
    | .falsum, some κ => return .refute (← PrettyPrinter.delab (p.carrier.getD (mkConst ``Rat))) κ cert.strict combo
    | .falsum, none => throwError "sage_certify: the daemon returned no κ for a `False` goal"
    | _, _ => return .direct combo
  closeAndEmit <| ← match built with
    | .witness point n => Checker.witness point n
    | .direct combo => Checker.linearCombination combo
    | .refute α κ strict combo => Checker.refute #[] α κ strict combo

end Veriphy
