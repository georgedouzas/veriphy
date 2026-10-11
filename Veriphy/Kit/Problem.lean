/-
Problem extraction: a Lean goal and its local context → one normalized constraint
problem, translated to Sage over a single shared atom table.

Every constraint is `lhs - rhs (rel) 0` with `rel ∈ {=, ≤, <, ≠}` (`≥`/`>` are
flipped, `¬ a = b` is `≠`). Hypotheses are collected only when they translate
(untranslatable ones are skipped with the atom table rolled back) and only when
their names can be written in source, so every constraint is referable from a
printed proof.
-/
import Veriphy.Translate

namespace Veriphy

open Lean Elab Tactic Meta

/-- A normalized relation: `p = 0`, `p ≤ 0`, `p < 0`, `p ≠ 0`. -/
inductive Rel | eq | le | lt | ne
  deriving BEq, Repr, Inhabited

/-- The daemon's relation tag. -/
def Rel.tag : Rel → String
  | .eq => "eq" | .le => "le" | .lt => "lt" | .ne => "ne"

/-- `(carrier, lhs, rhs, rel)` meaning `lhs - rhs (rel) 0`, for a proposition. -/
def relOf? (t : Expr) : Option (Expr × Expr × Expr × Rel) :=
  match t.getAppFnArgs with
  | (``Eq, #[α, a, b]) => some (α, a, b, .eq)
  | (``LE.le, #[α, _, a, b]) => some (α, a, b, .le)
  | (``LT.lt, #[α, _, a, b]) => some (α, a, b, .lt)
  | (``GE.ge, #[α, _, a, b]) => some (α, b, a, .le)
  | (``GT.gt, #[α, _, a, b]) => some (α, b, a, .lt)
  | (``Ne, #[α, a, b]) => some (α, a, b, .ne)
  | (``Not, #[p]) =>
    match p.getAppFnArgs with
    | (``Eq, #[α, a, b]) => some (α, a, b, .ne)
    | _ => none
  | _ => none

/-- One constraint `lhs - rhs (rel) 0`, with its Sage form and the hypothesis it came from. -/
structure Constraint where
  lhs : Expr
  rhs : Expr
  rel : Rel
  /-- Sage polynomial for `lhs - rhs`, over the problem's variables. -/
  poly : String
  /-- The source hypothesis (always a nameable user name), if any. -/
  src : Option Name := none
  deriving Inhabited

/-- The printable reference to a constraint's source hypothesis (as a proof term). -/
def Constraint.ref (c : Constraint) : MetaM (TSyntax `term) := do
  let some n := c.src | throwError "veriphy: constraint has no source hypothesis"
  return ⟨(mkIdent n).raw⟩

/-- The goal, classified. -/
inductive Goal
  | rel (c : Constraint)
  | falsum
  /-- `∃ binders, ⋀ body`; the binders are atoms `0 … n-1`. -/
  | exists_ (binders : Array Expr) (body : Array Constraint)
  deriving Inhabited

/-- A normalized problem. Atom `i` is the Sage variable `x{i}`. -/
structure Problem where
  carrier : Expr
  atoms : Array Expr
  hyps : Array Constraint
  goal : Goal
  /-- Extra terms the tactic asked to translate over the same atom table (e.g. `sage_sos` hints). -/
  extras : Array String := #[]

/-- The atom-table monad: translation state shared across one tactic invocation. -/
abbrev ProblemM := StateRefT (Array Expr) MetaM

/-- Run a translation; on failure restore the atom table and return `none`. -/
def tryTranslate {α : Type} (x : ProblemM α) : ProblemM (Option α) := do
  let saved ← get
  try some <$> x
  catch _ => set saved; pure none

/-- Translate one relation into a constraint over the shared atom table. -/
def Constraint.mk' (lhs rhs : Expr) (rel : Rel) (src : Option Name := none) : ProblemM Constraint := do
  let l ← exprToSage lhs
  let r ← exprToSage rhs
  return { lhs, rhs, rel, poly := s!"({l}) - ({r})", src }

/-- Which goals and hypotheses a tactic accepts. -/
structure ExtractOpts where
  /-- Tactic name, for error messages. -/
  tac : String
  /-- Relation goals accepted (after `≥`/`>` flips). -/
  goalRels : Array Rel := #[]
  allowFalse : Bool := false
  allowExists : Bool := false
  /-- Translate only the goal's left-hand side (the `rhs` is left to the residual goal). -/
  lhsOnly : Bool := false
  /-- Relations collected from the local context (empty: no hypotheses). -/
  hypRels : Array Rel := #[]
  /-- Refute a `≤`/`<` goal: treat the goal as `False` plus its negation as a hypothesis of this name. -/
  negateGoalAs : Option Name := none
  /-- Extra terms to translate after the goal and hypotheses. -/
  extras : Array Expr := #[]
  /-- Fail unless at least one hypothesis was collected. -/
  needHyps : Bool := false

/-- Can this hypothesis name be written in source? -/
def nameable (decl : LocalDecl) : Bool :=
  !decl.isImplementationDetail && !decl.userName.hasMacroScopes && !decl.userName.isInaccessibleUserName

private partial def conjuncts (e : Expr) : List Expr :=
  match e.getAppFnArgs with
  | (``And, #[a, b]) => conjuncts a ++ conjuncts b
  | _ => [e]

/-- Peel `∃ x₁ … xₙ, body`, binding the variables as local declarations, and run `k` on them. -/
private partial def peelExists {β : Type} (e : Expr) (vars : Array Expr)
    (k : Array Expr → Expr → TermElabM β) : TermElabM β := do
  match e.getAppFnArgs with
  | (``Exists, #[ty, .lam n _ body bi]) =>
    withLocalDecl n bi ty fun x => peelExists (body.instantiate1 x) (vars.push x) k
  | _ => k vars e

private def shapes (o : ExtractOpts) : String :=
  let rels := o.goalRels.toList.map fun
    | .eq => "`a = b`" | .le => "`a ≤ b`" | .lt => "`a < b`" | .ne => "`a ≠ b`"
  let all := rels ++ (if o.allowFalse then ["`False`"] else []) ++ (if o.allowExists then ["`∃ …`"] else [])
  ", ".intercalate all

/-- Collect the nameable context hypotheses of the carrier type with an accepted relation. -/
private def collectHyps (o : ExtractOpts) (carrier : Option Expr) :
    ProblemM (Option Expr × Array Constraint) := do
  let mut carrier := carrier
  let mut hyps := #[]
  if o.hypRels.isEmpty then return (carrier, hyps)
  for decl in ← getLCtx do
    unless nameable decl do continue
    let some (α, a, b, r) := relOf? (← instantiateMVars decl.type) | continue
    unless o.hypRels.contains r do continue
    match carrier with
    | none => carrier := some α
    | some β => unless ← withReducible (isDefEq α β) do continue
    if let some c ← tryTranslate (Constraint.mk' a b r decl.userName) then
      hyps := hyps.push c
  return (carrier, hyps)

/-- Extract the normalized problem for the main goal and run `k` on it. `k` runs in the goal's context
(extended with the peeled binders for an `∃` goal), so it may delaborate atoms; it should only *compute*
(call the daemon, build syntax) — closing the goal happens afterwards, in the original context. -/
def withProblem {α : Type} (o : ExtractOpts) (k : Problem → TermElabM α) : TacticM α := withMainContext do
  let tgt ← instantiateMVars (← (← getMainGoal).getType)
  let bad {β} : TermElabM β :=
    throwError "{o.tac}: goal must be {shapes o}, got{indentExpr tgt}"
  -- `goal` translates the goal and returns it with any hypotheses it contributes (a negated goal)
  let finish (carrier : Option Expr) (goal : ProblemM (Goal × Array Constraint)) (seed : Array Expr) :
      TermElabM α := do
    let ((goal, extraHyps, carrier, hyps, extras), atoms) ← (do
        let (goal, extraHyps) ← goal
        let (carrier, hyps) ← collectHyps o carrier
        let extras ← o.extras.mapM exprToSage
        pure (goal, extraHyps, carrier, hyps, extras)).run seed
    let some carrier := carrier
      | throwError "{o.tac}: no usable hypotheses in context"
    if o.needHyps && hyps.isEmpty then
      throwError "{o.tac}: no usable hypotheses in context"
    if atoms.isEmpty then
      throwError "{o.tac}: no variables found in the goal or hypotheses"
    k { carrier, atoms, hyps := hyps ++ extraHyps, goal, extras }
  if tgt.isConstOf ``False then
    unless o.allowFalse do bad
    finish none (pure (.falsum, #[])) #[]
  else if tgt.isAppOf ``Exists then
    unless o.allowExists do bad
    peelExists tgt #[] fun vars body => do
      if vars.isEmpty then bad
      let goal : ProblemM (Goal × Array Constraint) := do
        let mut cs := #[]
        for c in conjuncts body do
          let some (_, a, b, r) := relOf? c
            | throwError "{o.tac}: unsupported conjunct{indentExpr c}"
          cs := cs.push (← Constraint.mk' a b r)
        unless (← get).size == vars.size do
          throwError "{o.tac}: the body has free subterms other than the bound variables"
        pure (.exists_ vars cs, #[])
      finish (← inferType vars[0]!) goal vars
  else
    let some (α, a, b, r) := relOf? tgt | bad
    match o.negateGoalAs, r with
    | some h, .le | some h, .lt =>
      -- refutation: the goal becomes `False`, its negation a hypothesis (`¬ a ≤ b` is `b < a`, `¬ a < b` is `b ≤ a`)
      let nr := if r == .le then Rel.lt else Rel.le
      finish (some α) (do pure (.falsum, #[← Constraint.mk' b a nr h])) #[]
    | _, _ =>
      unless o.goalRels.contains r do bad
      let goal : ProblemM (Goal × Array Constraint) := do
        if o.lhsOnly then
          return (.rel { lhs := a, rhs := b, rel := r, poly := ← exprToSage a }, #[])
        return (.rel (← Constraint.mk' a b r), #[])
      finish (some α) goal #[]

/-- Delaborated atoms, for reconstruction (call inside `withProblem`'s continuation). -/
def Problem.atomStx (p : Problem) : TermElabM (Array (TSyntax `term)) :=
  p.atoms.mapM fun a => PrettyPrinter.delab a

/-- The Sage variable names, `x0 … x{n-1}`. -/
def Problem.vars (p : Problem) : List String := sageVarNames p.atoms

private def Constraint.toJson (c : Constraint) : Json :=
  Json.mkObj <| [("poly", Json.str c.poly), ("rel", Json.str c.rel.tag)] ++
    (match c.src with | some n => [("name", Json.str n.toString)] | none => [])

/-- Serialization for the daemon (`certify`): variables, a Lean rendering of each atom, the
hypotheses with names and relation tags, and the goal. -/
def Problem.toJson (p : Problem) : MetaM Json := do
  let atoms ← p.atoms.mapM fun a => return Json.str (toString (← ppExpr a))
  let goal := match p.goal with
    | .rel c => Json.mkObj [("kind", "rel"), ("poly", Json.str c.poly), ("rel", Json.str c.rel.tag)]
    | .falsum => Json.mkObj [("kind", "false")]
    | .exists_ bs body => Json.mkObj
        [("kind", "exists"), ("binders", Json.num bs.size), ("body", Json.arr (body.map (·.toJson)))]
  return Json.mkObj
    [ ("vars", Json.arr (p.vars.toArray.map Json.str))
    , ("atoms", Json.arr atoms)
    , ("hyps", Json.arr (p.hyps.map (·.toJson)))
    , ("goal", goal) ]

end Veriphy
