/-
Shared translation machinery for Veriphy certificate tactics.

Lean → Sage: `exprToSage` walks a ring expression; anything that is not
`+ - * ^ -ₙ` or a numeral becomes an atom `x0, x1, ...` (collected in state).

Sage → Lean: certificates arrive as structured term lists (`Bridge.Term`:
rational coefficient + exponent vector), reconstructed as term syntax over the
delaborated atoms. Nothing here is trusted: a bad reconstruction makes the
downstream kernel check fail, never a wrong proof.
-/
import Mathlib.Tactic.Ring
import Veriphy.Bridge

namespace Veriphy

open Lean Elab Meta

/-- Extract a `Nat` from a numeral expression (`OfNat` or raw literal). -/
partial def natLit? (e : Expr) : Option Nat :=
  match e with
  | .lit (.natVal n) => some n
  | _ =>
    match e.getAppFnArgs with
    | (``OfNat.ofNat, #[_, n, _]) => natLit? n
    | _ => none

/-- Translate a ring expression to Sage polynomial syntax. Atoms are collected
in the state and named `x0, x1, ...`. Unsupported shapes fail loudly. -/
partial def exprToSage (e : Expr) : StateRefT (Array Expr) MetaM String := do
  if let some n := natLit? e then
    return toString n
  match e.getAppFnArgs with
  | (``HAdd.hAdd, #[_, _, _, _, a, b]) =>
    return s!"({← exprToSage a} + {← exprToSage b})"
  | (``HSub.hSub, #[_, _, _, _, a, b]) =>
    return s!"({← exprToSage a} - {← exprToSage b})"
  | (``HMul.hMul, #[_, _, _, _, a, b]) =>
    return s!"({← exprToSage a} * {← exprToSage b})"
  | (``HPow.hPow, #[_, _, _, _, a, n]) =>
    let some k := natLit? n
      | throwError "veriphy: exponent must be a numeral, got {n}"
    return s!"({← exprToSage a})^{k}"
  | (``Neg.neg, #[_, _, a]) =>
    return s!"(-{← exprToSage a})"
  | _ =>
    let atoms ← get
    for h : i in [0:atoms.size] do
      if ← withReducible (isDefEq atoms[i] e) then
        return s!"x{i}"
    set (atoms.push e)
    return s!"x{atoms.size}"

/-- The variable names `exprToSage` assigned, in order, for the daemon. -/
def sageVarNames (atoms : Array Expr) : List String :=
  (List.range atoms.size).map (s!"x{·}")

/-- Parse Sage's rational string (`"-3/2"`, `"5"`) into numerator/denominator. -/
def parseRat (s : String) : Option (Int × Nat) :=
  match s.splitOn "/" with
  | [n] => n.toInt?.map (·, 1)
  | [n, d] => do pure (← n.toInt?, ← d.toNat?)
  | _ => none

/-- Rational literal as term syntax (`3`, `-3`, `3 / 2`, `-(3 / 2)`). -/
def ratStx (n : Int) (d : Nat) : TermElabM (TSyntax `term) := do
  let nlit : TSyntax `num := Syntax.mkNumLit (toString n.natAbs)
  let base : TSyntax `term ←
    if d == 1 then `($nlit:num)
    else
      let dlit : TSyntax `num := Syntax.mkNumLit (toString d)
      `($nlit:num / $dlit:num)
  if n < 0 then `(-$base) else pure base

/-- Parse a certificate rational or fail. -/
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

/-- A whole polynomial (term list) as syntax: sum of monomials. -/
def polyStx (atoms : Array (TSyntax `term)) (terms : List Bridge.Term) :
    TermElabM (TSyntax `term) := do
  let ts ← terms.toArray.mapM (termStx atoms)
  if ts.isEmpty then `(0)
  else ts[1:].foldlM (fun acc t => `($acc + $t)) ts[0]!

end Veriphy
