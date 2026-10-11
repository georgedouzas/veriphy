/-
Proof reconstruction: certificate data (untrusted, from Sage) → Lean syntax.

Everything built here is meant to be *printed* as a `Try this:` replacement and
pasted back, so every identifier is unhygienic: lemma and hypothesis references
are spliced in as `mkIdent` values (never written bare inside a quotation, where
hygiene would print them as `name✝`), and fresh locals come from `freshIdent`.
Nothing here is trusted: a bad reconstruction fails the downstream checker.
-/
import Lean
import Veriphy.Bridge

namespace Veriphy

open Lean Elab Meta

/-- Parse Sage's rational string (`"-3/2"`, `"5"`) into numerator/denominator. -/
def parseRat (s : String) : Option (Int × Nat) :=
  match s.splitOn "/" with
  | [n] => n.toInt?.map (·, 1)
  | [n, d] => do
    let d ← d.toNat?
    if d == 0 then none else pure (← n.toInt?, d)
  | _ => none

/-- Rational literal as term syntax (`3`, `-3`, `3 / 2`, `-(3 / 2)`). -/
def ratStx (n : Int) (d : Nat) : TermElabM (TSyntax `term) := do
  let nlit : TSyntax `num := Syntax.mkNumLit (toString n.natAbs)
  let base : TSyntax `term ←
    if d == 1 then `($nlit:num)
    else
      let dlit : TSyntax `num := Syntax.mkNumLit (toString d)
      `($nlit:num / $dlit:num)
  if n < 0 then
    if d == 1 then `(-$base) else `(-($base))
  else pure base

/-- Parse a certificate rational or fail, quoting the offending string. -/
def ratStx' (s : String) : TermElabM (TSyntax `term) := do
  let some (n, d) := parseRat s
    | throwError "veriphy: bad rational in certificate: {s}"
  ratStx n d

/-- One monomial `coeff * x₀^e₀ * ...` as syntax over the atom terms. -/
def termStx (atoms : Array (TSyntax `term)) (t : Bridge.Term) :
    TermElabM (TSyntax `term) := do
  let some (n, d) := parseRat t.coeff
    | throwError "veriphy: bad coefficient in certificate: {t.coeff}"
  let monos : Array (TSyntax `term) ← (atoms.zip t.exps.toArray).filterMapM
    fun (v, e) => do
      if e == 0 then return none
      else if e == 1 then return some v
      else
        let elit : TSyntax `num := Syntax.mkNumLit (toString e)
        return some (← `($v ^ $elit))
  if monos.isEmpty then
    ratStx n d
  else
    let prod ← monos[1:].foldlM (fun acc m => `($acc * $m)) monos[0]!
    if n == 1 && d == 1 then pure prod
    else if n == -1 && d == 1 then `(-$prod)
    else `($(← ratStx n d) * $prod)

/-- A whole polynomial (term list) as syntax: sum of monomials; the empty list is `0`. -/
def polyStx (atoms : Array (TSyntax `term)) (terms : List Bridge.Term) :
    TermElabM (TSyntax `term) := do
  let ts ← terms.toArray.mapM (termStx atoms)
  if ts.isEmpty then `(0)
  else ts[1:].foldlM (fun acc t => `($acc + $t)) ts[0]!

/-- A rational constant as a one-term polynomial (so weights and cofactors share one path). -/
def Bridge.Term.const (q : String) : List Bridge.Term := [{ coeff := q, exps := [] }]

/-- Is this term list the zero polynomial? -/
def isZeroPoly (terms : List Bridge.Term) : Bool :=
  terms.all fun t => parseRat t.coeff |>.any (·.1 == 0)

/-- Is this term list the constant `1`? -/
def isOnePoly (terms : List Bridge.Term) : Bool :=
  match terms with
  | [t] => t.exps.all (· == 0) && parseRat t.coeff == some (1, 1)
  | _ => false

/-- `w₁ * p₁ + … + wₖ * pₖ` for (weight polynomial, proof term) pairs. Zero weights are dropped and unit
weights omitted; an all-zero certificate is an error, never a silent `0`. -/
def weightedSum (atoms : Array (TSyntax `term)) (items : Array (List Bridge.Term × TSyntax `term)) :
    TermElabM (TSyntax `term) := do
  let mut pieces : Array (TSyntax `term) := #[]
  for (w, p) in items do
    if isZeroPoly w then continue
    if isOnePoly w then pieces := pieces.push p
    else pieces := pieces.push (← `(($(← polyStx atoms w)) * $p))
  if pieces.isEmpty then throwError "veriphy: empty certificate (every weight is zero)"
  pieces[1:].foldlM (fun acc p => `($acc + $p)) pieces[0]!

/-- An anonymous-constructor witness `⟨v₁, …, vₙ, proof⟩`, checking the arity against the binders. -/
def witnessStx (values : List String) (binders : Nat) (proof : TSyntax `term) :
    TermElabM (TSyntax `term) := do
  unless values.length == binders do
    throwError "veriphy: witness has {values.length} values for {binders} binders"
  let vals ← values.toArray.mapM ratStx'
  `(⟨$[$vals],*, $proof⟩)

/-- Several tactic steps as one block, run and printed as a unit. -/
def stepsStx (steps : Array (TSyntax `tactic)) : CoreM (TSyntax `tactic) := do
  if h : steps.size = 1 then return steps[0]
  `(tactic| ($[$steps]*))

/-- A fresh, unhygienic local name: `base`, or `base_1`, … if `base` is taken in the current context. -/
def freshIdent (base : Name) : MetaM Ident := do
  return mkIdent ((← getLCtx).getUnusedName base)

/-- A reference to a hypothesis by its user name (extraction only collects nameable ones). -/
def hypIdent (n : Name) : Ident := mkIdent n

end Veriphy
