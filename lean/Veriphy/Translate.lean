/-
Shared translation machinery for Veriphy certificate tactics.

Lean → Sage: `exprToSage` walks a ring expression; anything that is not
`+ - * ^ -ₙ`, a numeral, or a division by a numeral (a rational coefficient)
becomes an atom `x0, x1, ...` (collected in state).

-/
import Mathlib.Tactic.Ring
import Lean

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
  | (``HDiv.hDiv, #[_, _, _, _, a, b]) =>
    -- division by a nonzero numeral is a rational coefficient; any other division is an atom
    match natLit? b with
    | some d =>
      if d == 0 then atom e else return s!"({← exprToSage a} / {d})"
    | none => atom e
  | (``Inv.inv, #[_, _, b]) =>
    match natLit? b with
    | some d => if d == 0 then atom e else return s!"(1 / {d})"
    | none => atom e
  | _ => atom e
where
  /-- Register `e` as an indeterminate (reusing a definitionally equal atom). -/
  atom (e : Expr) : StateRefT (Array Expr) MetaM String := do
    let atoms ← get
    for h : i in [0:atoms.size] do
      if ← withReducible (isDefEq atoms[i] e) then
        return s!"x{i}"
    set (atoms.push e)
    return s!"x{atoms.size}"

/-- The variable names `exprToSage` assigned, in order, for the daemon. -/
def sageVarNames (atoms : Array Expr) : List String :=
  (List.range atoms.size).map (s!"x{·}")

end Veriphy
