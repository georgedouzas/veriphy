/-
`sage_factor`: the first Veriphy certificate tactic.

On a goal `lhs = rhs`, the tactic:
  1. translates `lhs` into a polynomial over ℚ (atoms become variables),
  2. asks the Sage daemon for a factorization certificate (structured term
     lists, see `Veriphy.Bridge`),
  3. rebuilds `unit * ∏ fᵢ ^ mᵢ` as a Lean term,
  4. proves `lhs = factored` with `ring1` — the kernel-checked step; Sage's
     answer is verified, never trusted — and
  5. leaves the goal `factored = rhs`, emitting a `Try this:` replacement
     (`refine Eq.trans (show lhs = factored by ring1) ?_`) so the committed
     proof checks without Sage installed.

Also provides the `#sage_factor` diagnostic command.
-/
import Mathlib.Tactic.Ring
import Veriphy.Bridge

namespace Veriphy

open Lean Elab Tactic Meta Bridge

/-! ## Lean → Sage translation -/

/-- Extract a `Nat` from a numeral expression (`OfNat` or raw literal). -/
private partial def natLit? (e : Expr) : Option Nat :=
  match e with
  | .lit (.natVal n) => some n
  | _ =>
    match e.getAppFnArgs with
    | (``OfNat.ofNat, #[_, n, _]) => natLit? n
    | _ => none

/-- Translate a ring expression to Sage polynomial syntax. Atoms (anything that
is not `+ - * ^ -ₙ` or a numeral) are collected in the state and named `x0,
x1, ...`. Unsupported shapes fail loudly. -/
private partial def exprToSage (e : Expr) : StateRefT (Array Expr) MetaM String := do
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
      | throwError "sage_factor: exponent must be a numeral, got {n}"
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

/-! ## Certificate → Lean term reconstruction -/

/-- Parse Sage's rational string (`"-3/2"`, `"5"`) into numerator/denominator. -/
private def parseRat (s : String) : Option (Int × Nat) :=
  match s.splitOn "/" with
  | [n] => n.toInt?.map (·, 1)
  | [n, d] => do pure (← n.toInt?, ← d.toNat?)
  | _ => none

private def ratStx (n : Int) (d : Nat) : TermElabM (TSyntax `term) := do
  let nlit : TSyntax `num := Syntax.mkNumLit (toString n.natAbs)
  let base : TSyntax `term ←
    if d == 1 then `($nlit:num)
    else
      let dlit : TSyntax `num := Syntax.mkNumLit (toString d)
      `($nlit:num / $dlit:num)
  if n < 0 then `(-$base) else pure base

/-- One monomial `coeff * x₀^e₀ * ...` as syntax over the atom terms. -/
private def termStx (atoms : Array (TSyntax `term)) (t : Bridge.Term) :
    TermElabM (TSyntax `term) := do
  let some (n, d) := parseRat t.coeff
    | throwError "sage_factor: bad coefficient in certificate: {t.coeff}"
  let monos : Array (TSyntax `term) ← (atoms.zip t.exps.toArray).filterMapM
    fun (v, e) => do
      if e == 0 then return none
      else if e == 1 then return some v
      else
        let elit : TSyntax `num := Syntax.mkNumLit (toString e)
        return some (← `($v ^ $elit))
  -- drop a redundant `1 *` / fold `-1 *` into negation when monomials exist
  if monos.isEmpty then
    ratStx n d
  else
    let prod ← monos[1:].foldlM (fun acc m => `($acc * $m)) monos[0]!
    if n == 1 && d == 1 then pure prod
    else if n == -1 && d == 1 then `(-$prod)
    else `($(← ratStx n d) * $prod)

private def factorStx (atoms : Array (TSyntax `term)) (f : Bridge.Factor) :
    TermElabM (TSyntax `term) := do
  let ts ← f.terms.toArray.mapM (termStx atoms)
  if ts.isEmpty then throwError "sage_factor: empty factor in certificate"
  let sum ← ts[1:].foldlM (fun acc t => `($acc + $t)) ts[0]!
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

/-! ## The tactic -/

/-- `sage_factor` — on a goal `lhs = rhs`, replace it with `factored = rhs`
where `factored` is Sage's factorization of `lhs`, certified in-kernel by
`ring1`. Emits a `Try this:` replacement that checks without Sage. -/
elab (name := sageFactor) ref:"sage_factor" : tactic => withMainContext do
  let goal ← getMainGoal
  let tgt ← instantiateMVars (← goal.getType)
  let some (α, lhs, rhs) := tgt.eq?
    | throwError "sage_factor: goal must be an equality, got{indentExpr tgt}"
  -- 1. translate
  let (polyStr, atoms) ← (exprToSage lhs).run #[]
  if atoms.isEmpty then
    throwError "sage_factor: no variables found in{indentExpr lhs}"
  let varNames := (List.range atoms.size).map (s!"x{·}")
  -- 2. untrusted oracle call
  let cert ← Bridge.factor polyStr varNames
  -- 3. reconstruct
  let atomStx ← atoms.mapM fun a => PrettyPrinter.delab a
  let fstx ← certStx atomStx cert
  let f ← Term.elabTermEnsuringType fstx (some α)
  Term.synthesizeSyntheticMVarsNoPostponing
  -- 4. certify: lhs = factored, by ring1 (the only trusted step)
  let hGoal ← mkFreshExprMVar (← mkEq lhs f)
  let remaining ← Tactic.run hGoal.mvarId! (evalTactic (← `(tactic| ring1)))
  unless remaining.isEmpty do
    throwError "sage_factor: certificate check failed — `ring1` could not \
      verify{indentExpr (← mkEq lhs f)}"
  -- 5. hand back `factored = rhs`
  let newGoal ← mkFreshExprMVar (← mkEq f rhs)
  goal.assign (← mkAppM ``Eq.trans #[hGoal, newGoal])
  replaceMainGoal [newGoal.mvarId!]
  let lhsStx ← PrettyPrinter.delab lhs
  let trans := mkIdent ``Eq.trans
  Lean.Meta.Tactic.TryThis.addSuggestion ref
    (← `(tactic| refine $trans (show $lhsStx = $fstx by ring1) ?_))
    (header := "Sage-free replacement: ")

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
