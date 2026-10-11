/-
`sage_exists`: rational witnesses. On a goal `∃ x₁ … xₙ, P` where `P` is a conjunction of polynomial
equations, linear inequalities and disequalities with no other free variables, Sage finds a rational point and
Lean checks it with `norm_num`. Typical uses: null vectors and eigenvectors (`A v = λ B v`, `v ≠ 0`),
explicit counterexamples, feasible charge assignments.
-/
import Mathlib.Tactic.NormNum
import Veriphy.Translate

namespace Veriphy

open Lean Elab Tactic Meta Bridge

private partial def conjuncts (e : Expr) : List Expr :=
  match e.getAppFnArgs with
  | (``And, #[a, b]) => conjuncts a ++ conjuncts b
  | _ => [e]

/-- Peel `∃ x₁ … xₙ, body`, binding the variables as local declarations, and run `k` on them. -/
private partial def peelExists {β : Type} (e : Expr) (vars : Array Expr)
    (k : Array Expr → Expr → MetaM β) : MetaM β := do
  match e.getAppFnArgs with
  | (``Exists, #[ty, .lam n _ body bi]) =>
    withLocalDecl n bi ty fun x => peelExists (body.instantiate1 x) (vars.push x) k
  | _ => k vars e

/-- `sage_exists` — close `∃ x₁ … xₙ, P` with a Sage-found rational witness checked by `norm_num`. -/
elab (name := sageExists) ref:"sage_exists" : tactic => withMainContext do
  let tgt ← instantiateMVars (← (← getMainGoal).getType)
  let pt ← peelExists tgt #[] fun vars body => do
    if vars.isEmpty then throwError "sage_exists: goal must start with `∃`"
    let atomsRef ← IO.mkRef vars
    let runTr (e : Expr) : MetaM String := do
      let (s, atoms) ← (exprToSage e).run (← atomsRef.get)
      atomsRef.set atoms
      return s
    let mut eqs : List String := []
    let mut les : List String := []
    let mut lts : List String := []
    let mut nes : List String := []
    for c in conjuncts body do
      match c.getAppFnArgs with
      | (``Eq, #[_, a, b]) => eqs := eqs ++ [s!"({← runTr a}) - ({← runTr b})"]
      | (``LE.le, #[_, _, a, b]) => les := les ++ [s!"({← runTr a}) - ({← runTr b})"]
      | (``LT.lt, #[_, _, a, b]) => lts := lts ++ [s!"({← runTr a}) - ({← runTr b})"]
      | (``GE.ge, #[_, _, a, b]) => les := les ++ [s!"({← runTr b}) - ({← runTr a})"]
      | (``GT.gt, #[_, _, a, b]) => lts := lts ++ [s!"({← runTr b}) - ({← runTr a})"]
      | (``Ne, #[_, a, b]) => nes := nes ++ [s!"({← runTr a}) - ({← runTr b})"]
      | (``Not, #[p]) =>
        match p.getAppFnArgs with
        | (``Eq, #[_, a, b]) => nes := nes ++ [s!"({← runTr a}) - ({← runTr b})"]
        | _ => throwError "sage_exists: unsupported conjunct{indentExpr c}"
      | _ => throwError "sage_exists: unsupported conjunct{indentExpr c}"
    let atoms ← atomsRef.get
    unless atoms.size == vars.size do
      throwError "sage_exists: the body has free subterms other than the bound variables"
    Bridge.exists_ (sageVarNames atoms) eqs les lts nes
  let vals : Array (TSyntax `term) ← pt.toArray.mapM fun v => liftM (m := TermElabM) (ratStx' v)
  let proof ← `(tactic| exact ⟨$[$vals],*, by norm_num⟩)
  evalTactic proof
  Lean.Meta.Tactic.TryThis.addSuggestion ref proof (header := "Sage-free replacement: ")

end Veriphy
