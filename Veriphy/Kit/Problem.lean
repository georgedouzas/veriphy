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
import Veriphy.Kit.Symbolic
import Veriphy.Kit.Packs

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
  /-- The proposition the constraint came from, for its Lean text. -/
  prop : Option Expr := none
  /-- Sage polynomials of `lhs` and `rhs` on their own. -/
  lhsPoly : String := ""
  rhsPoly : String := ""
  /-- Sage symbolic form of `lhs - rhs` (set by the symbolic pass). -/
  expr : Option String := none
  deriving Inhabited

/-- The goal, classified. -/
inductive Goal
  | rel (c : Constraint)
  | falsum
  /-- `∃ binders, ⋀ body`; the binders are atoms `0 … n-1`. -/
  | exists_ (binders : Array Expr) (body : Array Constraint)
  /-- Any other proposition, with no polynomial form (lenient extraction only). -/
  | other (prop : Expr)
  deriving Inhabited

/-- A normalized problem. Atom `i` is the Sage variable `x{i}`. -/
structure Problem where
  /-- The type the polynomials live in, when the goal or a hypothesis fixes one. -/
  carrier : Option Expr
  atoms : Array Expr
  hyps : Array Constraint
  goal : Goal
  /-- Nameable hypotheses with no polynomial form, kept as text (lenient extraction only), with their
  symbolic form when they are relations. -/
  facts : Array (Name × Expr) := #[]
  factExprs : Array (Option (String × String)) := #[]
  /-- The symbolic form of an `other` goal that is a relation. -/
  goalExpr : Option (String × String) := none
  /-- The Lean type of each atom: `ℕ`, `ℤ`, `ℚ`, `ℝ`, `ℂ`, `matrix` or `other`. -/
  atomTypes : Array String := #[]
  /-- Domain conditions: the Sage term, the kind (`ne`, `nonneg`, `pos`), its Lean text, and the hypothesis
  that discharges it. -/
  conditions : Array (String × String × Option String × Expr × Option Name) := #[]
  /-- The translation namespaces in force, core first. -/
  namespaces : List String := []
  /-- Problems found resolving the translation tables (missing constants, conflicts). -/
  tableProblems : Array String := #[]
  /-- The project's table entries the problem uses, serialized for the daemon. -/
  extensions : List Table := []
  /-- The derivatives the translation met: variable, body and point in Sage syntax, function and point in Lean. -/
  derivatives : Array (String × String × String × String × String) := #[]
  /-- The unknown functions met: Sage name, Lean name, arity. -/
  functions : Array (String × String × Nat) := #[]
  /-- Explicit definitions of unknown functions from hypotheses `x = fun t => body`: Sage name, variable, body. -/
  definitions : Array (String × String × String) := #[]

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
  return { lhs, rhs, rel, poly := s!"({l}) - ({r})", src, lhsPoly := l, rhsPoly := r }

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

/-- Translate a hypothesis to a constraint when it is a relation over the carrier (or fixes a missing one),
returning the carrier it used. -/
private def translateHyp (carrier : Option Expr) (decl : LocalDecl) (ty : Expr) :
    ProblemM (Option (Expr × Constraint)) := do
  let some (α, a, b, r) := relOf? ty | return none
  if let some β := carrier then
    unless ← withReducible (isDefEq α β) do return none
  let some c ← tryTranslate (Constraint.mk' a b r decl.userName) | return none
  return some (α, { c with prop := ty })

/-- Collect every nameable hypothesis that is a proposition: as a constraint when it is a relation over the
carrier that translates, otherwise as a text-only fact. -/
private def collectAll (carrier : Option Expr) :
    ProblemM (Option Expr × Array Constraint × Array (Name × Expr)) := do
  let mut carrier := carrier
  let mut hyps := #[]
  let mut facts := #[]
  for decl in ← getLCtx do
    unless nameable decl do continue
    let ty ← instantiateMVars decl.type
    unless ← isProp ty do continue
    match ← translateHyp carrier decl ty with
    | some (α, c) =>
      carrier := carrier <|> some α
      hyps := hyps.push c
    | none => facts := facts.push (decl.userName, ty)
  return (carrier, hyps, facts)

/-- The relation tag and symbolic form `(a) - (b)` of a relation `a rel b`, over the shared atom table. -/
private def relSym (prop : Expr) : SymM (Option (String × String)) := do
  let some (_, a, b, r) := relOf? prop | return none
  return some (r.tag, s!"({(← exprToSym a).toSage}) - ({(← exprToSym b).toSage})")

private def kindTag : DomainKind → String
  | .ne => "ne" | .nonneg => "nonneg" | .pos => "pos" | .le => "le"

/-- Add symbolic forms, atom types and domain conditions to an extracted problem. Atoms the symbolic
pass meets (such as `x` inside `Real.sin x`) are appended to the shared table. -/
def Problem.enrich (p : Problem) : MetaM Problem := do
  let constraintSym (c : Constraint) : SymM Constraint := do
    match c.prop with
    | some e => return { c with expr := (← relSym e).map (·.2) }
    | none => return { c with expr := some s!"({(← exprToSym c.lhs).toSage}) - ({(← exprToSym c.rhs).toSage})" }
  let symPass : SymM (Array Constraint × Array (Option (String × String)) × Goal × Option (String × String)) := do
      let hyps ← p.hyps.mapM constraintSym
      let factExprs ← p.facts.mapM fun (_, e) => relSym e
      let (goal, goalExpr) ← match p.goal with
        | .rel c => pure (Goal.rel (← constraintSym c), none)
        | .exists_ bs body => pure (Goal.exists_ bs (← body.mapM constraintSym), none)
        | .other e => pure (Goal.other e, ← relSym e)
        | .falsum => pure (Goal.falsum, none)
      pure (hyps, factExprs, goal, goalExpr)
  let (project, loadProblems) ← projectTables (veriphy.translationsDir.get (← getOptions))
  let (tables, resolveProblems) ← activeTables project
  let tableProblems := loadProblems ++ resolveProblems
  let ((hyps, factExprs, goal, goalExpr), st) ← symPass.run { atoms := p.atoms, tables }
  let mut conditions := #[]
  let mut seen : Array Condition := #[]
  for c in st.conditions do
    if ← seen.anyM (·.same c) then continue
    seen := seen.push c
    let (sage, _) ← (exprToSym c.term).run { atoms := st.atoms }
    let bound ← c.bound.mapM fun b => return (← (exprToSym b).run' { atoms := st.atoms }).toSage
    conditions := conditions.push (sage.toSage, kindTag c.kind, bound, ← c.prop, ← c.dischargedBy nameable)
  let atomTypes ← st.atoms.mapM atomType
  let p := { p with atoms := st.atoms, hyps, goal, factExprs, goalExpr, atomTypes, conditions }
  -- the project entries the translation used travel with the problem, so the daemon renders with them
  let used := st.usedEntries
  let extensions := (tables.filter (·.«namespace» == "project")).map fun t =>
    { t with functions := t.functions.filter (used.contains ·.lean),
             constants := t.constants.filter (used.contains ·.lean) }
  let derivatives := st.derivatives.map fun (k, b, pt, f, at_) => (k, b.toSage, pt.toSage, f, at_)
  -- hypotheses `x = fun t => body` define unknown functions explicitly
  let mut definitions := #[]
  for (sageName, f) in st.functions do
    for decl in ← getLCtx do
      unless nameable decl do continue
      let some (_, lhs, rhs, .eq) := relOf? (← instantiateMVars decl.type) | continue
      unless lhs == f do continue
      let .lam n ty body bi := rhs | continue
      let body' ← withLocalDecl n bi ty fun x => do
        let state : SymState := { atoms := st.atoms, tables := tables, bound := #[(x, "s_")] }
        let (sym, _) ← (exprToSym (body.instantiate1 x)).run { state with functions := st.functions }
        return sym.toSage
      definitions := definitions.push (sageName, "s_", body')
  let functions ← st.functions.mapM fun (sageName, f) => do
    let arity := (← forallTelescopeReducing (← inferType f) fun xs _ => pure xs.size)
    return (sageName, toString (← f.fvarId!.getUserName), arity)
  let p : Problem := { p with namespaces := tables.map (·.«namespace»), tableProblems := tableProblems }
  let p : Problem := { p with extensions := extensions, derivatives := derivatives }
  return { p with functions := functions, definitions := definitions }

/-- Extract the main goal and every nameable hypothesis, never rejecting a goal: anything without a
polynomial form is kept with its text. Runs `k` in the goal's context (extended with the binders of an
`∃` goal whose body translates). -/
def withLenientProblem {α : Type} (k : Problem → TermElabM α) : TacticM α := withMainContext do
  let tgt ← instantiateMVars (← (← getMainGoal).getType)
  let finish (carrier : Option Expr) (goal : ProblemM Goal) (seed : Array Expr) : TermElabM α := do
    let ((goal, (carrier, hyps, facts)), atoms) ← (do
        let goal ← goal
        pure (goal, ← collectAll carrier)).run seed
    k (← Problem.enrich { carrier, atoms, hyps, goal, facts })
  let other : ProblemM Goal := pure (.other tgt)
  if tgt.isConstOf ``False then
    finish none (pure .falsum) #[]
  else if tgt.isAppOf ``Exists then
    peelExists tgt #[] fun vars body => do
      let goal : ProblemM Goal := do
        let mut cs := #[]
        for c in conjuncts body do
          let some (_, a, b, r) := relOf? c | return .other tgt
          let some con ← tryTranslate (Constraint.mk' a b r) | return .other tgt
          cs := cs.push { con with prop := c }
        unless (← get).size == vars.size do return .other tgt
        pure (.exists_ vars cs)
      if vars.isEmpty then finish none other #[] else finish (← inferType vars[0]!) goal vars
  else
    match relOf? tgt with
    | some (α, a, b, r) =>
      let goal : ProblemM Goal := do
        match ← tryTranslate (Constraint.mk' a b r) with
        | some c => pure (.rel { c with prop := tgt })
        | none => pure (.other tgt)
      finish (some α) goal #[]
    | none => finish none other #[]

/-- The Sage variable names, `x0 … x{n-1}`. -/
def Problem.vars (p : Problem) : List String := sageVarNames p.atoms

private def text (e : Expr) : MetaM Json := return Json.str (toString (← ppExpr e))

private def Constraint.toJson (c : Constraint) : MetaM Json := do
  let base := [("poly", Json.str c.poly), ("rel", Json.str c.rel.tag)] ++
    (match c.src with | some n => [("name", Json.str n.toString)] | none => []) ++
    (match c.expr with | some x => [("expr", Json.str x)] | none => [])
  match c.prop with
  | some e => return Json.mkObj (base ++ [("text", ← text e)])
  | none => return Json.mkObj base

/-- Serialization for the daemon: variables, a Lean rendering of each atom, the carrier type, the
hypotheses (with names, relation tags and text; text only for facts), and the goal. -/
def Problem.toJson (p : Problem) : MetaM Json := do
  let atoms ← p.atoms.mapM text
  let goal ← match p.goal with
    | .rel c => do
      let textField ← match c.prop with
        | some e => pure [("text", ← text e)]
        | none => pure []
      let base : List (String × Json) := [("kind", Json.str "rel"), ("poly", Json.str c.poly), ("rel", Json.str c.rel.tag)] ++
        (match c.expr with | some x => [("expr", Json.str x)] | none => [])
      let lhsText ← text c.lhs
      let rhsText ← text c.rhs
      let sides : List (String × Json) := if c.lhsPoly.isEmpty then [] else
        [("lhs", lhsText), ("rhs", rhsText), ("lhs_poly", Json.str c.lhsPoly), ("rhs_poly", Json.str c.rhsPoly)]
      pure <| Json.mkObj (base ++ textField ++ sides)
    | .falsum => pure <| Json.mkObj [("kind", "false")]
    | .exists_ bs body => do
      pure <| Json.mkObj [("kind", "exists"), ("binders", Json.num bs.size),
        ("body", Json.arr (← body.mapM (·.toJson)))]
    | .other e => do
      let exprField : List (String × Json) := match p.goalExpr with
        | some (r, x) => [("expr", Json.str x), ("rel", Json.str r)] | none => []
      pure <| Json.mkObj ([("kind", Json.str "other"), ("text", ← text e)] ++ exprField)
  let facts ← (p.facts.zip (p.factExprs ++ Array.replicate p.facts.size none)).mapM fun ((n, e), x) => do
    let exprField : List (String × Json) := match x with
      | some (r, x) => [("expr", Json.str x), ("rel", Json.str r)] | none => []
    return Json.mkObj ([("name", Json.str n.toString), ("text", ← text e)] ++ exprField)
  let conditions ← p.conditions.mapM fun (sage, kind, bound, prop, discharge) => do
    let byField : List (String × Json) := match discharge with | some n => [("discharged_by", Json.str n.toString)] | none => []
    let boundField : List (String × Json) := match bound with | some b => [("bound", Json.str b)] | none => []
    return Json.mkObj ([("expr", Json.str sage), ("kind", Json.str kind), ("text", ← text prop)] ++ boundField ++ byField)
  let carrier ← match p.carrier with | some c => text c | none => pure (Json.str "")
  return Json.mkObj
    [ ("vars", Json.arr (p.vars.toArray.map Json.str))
    , ("atoms", Json.arr atoms)
    , ("carrier", carrier)
    , ("hyps", Json.arr ((← p.hyps.mapM (·.toJson)) ++ facts))
    , ("goal", goal)
    , ("atom_types", Json.arr (p.atomTypes.map Json.str))
    , ("domain", Json.arr conditions)
    , ("namespaces", Json.arr (p.namespaces.toArray.map Json.str))
    , ("table_problems", Json.arr (p.tableProblems.map Json.str))
    , ("extensions", Json.arr (p.extensions.toArray.map (Lean.toJson ·)))
    , ("derivatives", Json.arr (p.derivatives.map fun (k, b, pt, f, at_) =>
        Json.mkObj [("var", Json.str k), ("body", Json.str b), ("point", Json.str pt), ("function", Json.str f),
          ("at", Json.str at_)]))
    , ("functions", Json.arr (p.functions.map fun (s, l, a) =>
        Json.mkObj [("sage", Json.str s), ("lean", Json.str l), ("arity", Json.num a)]))
    , ("definitions", Json.arr (p.definitions.map fun (s, v, b) =>
        Json.mkObj [("function", Json.str s), ("var", Json.str v), ("body", Json.str b)])) ]

end Veriphy
