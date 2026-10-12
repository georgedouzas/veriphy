/-
Coverage of the symbolic translation on a corpus of statements (Sage-free).

`#veriphy_coverage [Prefix, …]` walks the theorems declared in modules whose name starts with one of the prefixes
(or, for the current file, whose own name does), opens their binders and translates every relation (`=`, `≠`, `≤`,
`<`, `≥`, `>`) in the hypotheses and the conclusion. Each atom of a translation is classified:

* local: a bound variable, a numeral left untranslated, or a structure projection of a bound variable (`x.val`,
  `p.1`), which is a variable in all but name;
* uninterpreted: an application whose function is a bound variable, such as `f x`, including bundled maps applied
  through their coercion (`DFunLike.coe f x` with `f` a variable);
* opaque: a term whose head is a global constant the translation does not know, such as `Real.Gamma x`.

A statement is fully covered when every atom is local. The report gives the shares, the most frequent opaque heads
(each counted once per statement) and, unless `veriphy.coverage.write` is off, writes JSON under
`.veriphy/coverage/`.
-/
import Veriphy.Kit.Problem
import Veriphy.Kit.Project

namespace Veriphy.Coverage

open Lean Elab Command Meta

register_option veriphy.coverage.write : Bool := {
  defValue := true
  descr := "write #veriphy_coverage reports under .veriphy/coverage/"
}

/-- How an atom of a translation is classified. -/
inductive AtomKind
  | local
  | uninterpreted
  | opaque (head : Name)
  deriving BEq, Inhabited

/-- Is `e` a variable, possibly behind structure projections (`x.val`, `p.1.2`)? -/
partial def isProjectedVariable (env : Environment) (e : Expr) : Bool :=
  if e.isFVar then true else
  match e with
  | .proj _ _ s => isProjectedVariable env s
  | _ =>
    match e.getAppFn with
    | .const n _ =>
      -- a projection applied to exactly its parameters and the structure, not a coercion applied further
      match env.getProjectionFnInfo? n with
      | some info => e.getAppNumArgs == info.numParams + 1 && isProjectedVariable env e.appArg!
      | none => false
    | _ => false

/-- Classify one atom by the head of its application. -/
def classify (env : Environment) (e : Expr) : AtomKind :=
  if isProjectedVariable env e then .local else
  match e.getAppFn with
  | .fvar _ => .uninterpreted
  | .lit _ => .local
  | .const ``DFunLike.coe _ =>
    match e.getAppArgs[4]? with
    | some f => if isProjectedVariable env f || f.getAppFn.isFVar then .uninterpreted else .opaque ``DFunLike.coe
    | none => .opaque ``DFunLike.coe
  | .const n _ => .opaque n
  | .proj s _ _ => .opaque s
  | _ => .opaque `«<other>»

/-- What one statement contributes: how many relations it has, and the kinds of their atoms. -/
structure Acc where
  relations : Nat := 0
  kinds : Array AtomKind := #[]

/-- A relation whose sides are data rather than propositions or functions. -/
private def dataRelation? (p : Expr) : MetaM (Option (Expr × Expr)) := do
  let some (α, a, b, _) := relOf? p | return none
  let α ← whnfR α
  if α.isForall || α.isProp || α.isSort then return none
  return some (a, b)

/-- Translate both sides of a relation and record the kinds of the atoms it needed. -/
private def recordRelation (a b : Expr) : StateRefT Acc MetaM Unit := do
  let (_, st) ← (do let _ ← exprToSym a; let _ ← exprToSym b).run { atoms := #[] }
  let env ← getEnv
  modify fun acc => { acc with relations := acc.relations + 1, kinds := acc.kinds ++ st.atoms.map (classify env) }

/-- Visit a proposition: record its relations, looking through `∧`, `∨`, `↔`, `¬`, `∃` and `∀`. -/
partial def visit (p : Expr) : StateRefT Acc MetaM Unit := do
  if let some (a, b) ← dataRelation? p then return ← recordRelation a b
  match p.getAppFnArgs with
  | (``And, #[x, y]) | (``Or, #[x, y]) | (``Iff, #[x, y]) => visit x; visit y
  | (``Not, #[x]) => visit x
  | (``Exists, #[_, .lam n ty body bi]) =>
    withLocalDecl n bi ty fun x => visit (body.instantiate1 x)
  | _ =>
    if p.isForall then
      forallTelescope p fun xs body => do
        for x in xs do
          let ty ← inferType x
          if ← isProp ty then visit ty
        visit body

/-- The contribution of one theorem statement. -/
def statementAcc (type : Expr) : MetaM Acc := do
  let ((), acc) ← (visit type).run {}
  return acc

/-- The result for one statement: whether it has a relation, is fully covered, is covered up to uninterpreted
functions, and which opaque heads it uses. -/
structure Verdict where
  name : Name
  hasRelation : Bool
  full : Bool
  upToUninterpreted : Bool
  heads : Array Name

/-- Judge one statement from its atoms. -/
def judge (name : Name) (acc : Acc) : Verdict :=
  let heads := acc.kinds.foldl (init := #[]) fun hs k =>
    match k with | .opaque h => if hs.contains h then hs else hs.push h | _ => hs
  { name, hasRelation := acc.relations > 0,
    full := acc.kinds.all (· == .local),
    upToUninterpreted := heads.isEmpty, heads }

/-- Does the theorem belong to the corpus: its module (or, for the current file, its name) starts with a prefix? -/
def inCorpus (env : Environment) (prefixes : Array Name) (n : Name) : Bool :=
  let source := match env.getModuleIdxFor? n with
    | some idx => env.header.moduleNames[idx.toNat]!
    | none => n
  prefixes.any (·.isPrefixOf source)

/-- Suffixes of lemmas Lean and mathlib generate (congruence, equation and injectivity lemmas). -/
def generatedSuffixes : List String := ["congr_simp", "eq_def", "injEq", "inj", "sizeOf_spec"]

/-- Is the theorem generated rather than stated by an author? -/
def isGenerated (n : Name) : Bool :=
  n.isInternalDetail ||
    match n with
    | .str _ s => generatedSuffixes.contains s || (s.startsWith "eq_" && (s.drop 3).all Char.isDigit)
    | _ => false

/-- The theorems of the corpus, skipping internal and generated declarations. -/
def corpus (env : Environment) (prefixes : Array Name) : Array (Name × Expr) :=
  env.constants.fold (init := #[]) fun acc n info =>
    match info with
    | .thmInfo t => if !isGenerated n && inCorpus env prefixes n then acc.push (n, t.type) else acc
    | _ => acc

/-- The aggregated report. -/
structure Report where
  prefixes : Array Name
  theorems : Nat
  withRelation : Nat
  full : Nat
  upToUninterpreted : Nat
  failed : Nat
  /-- Opaque heads with their statement counts and one example statement, most frequent first. -/
  heads : Array (Name × Nat × Name)

/-- How many heads the report lists. -/
def topHeads : Nat := 30

/-- Aggregate verdicts into a report. -/
def aggregate (prefixes : Array Name) (theorems failed : Nat) (vs : Array Verdict) : Report := Id.run do
  let rel := vs.filter (·.hasRelation)
  let mut counts : Std.HashMap Name (Nat × Name) := {}
  for v in rel do
    for h in v.heads do
      counts := counts.insert h (match counts[h]? with | some (c, ex) => (c + 1, ex) | none => (1, v.name))
  let sorted := counts.toArray.map (fun (h, c, ex) => (h, c, ex))
    |>.qsort fun (h₁, c₁, _) (h₂, c₂, _) => c₁ > c₂ || (c₁ == c₂ && h₁.toString < h₂.toString)
  return { prefixes, theorems, withRelation := rel.size, full := (rel.filter (·.full)).size,
           upToUninterpreted := (rel.filter (·.upToUninterpreted)).size, failed, heads := sorted }

/-- A share as a percentage with one decimal. -/
def percent (part whole : Nat) : String :=
  if whole == 0 then "n/a" else
    let tenths := (part * 1000 + whole / 2) / whole
    s!"{tenths / 10}.{tenths % 10}%"

/-- The report as JSON. -/
def Report.toJson (r : Report) : Json :=
  Json.mkObj [
    ("prefixes", Json.arr (r.prefixes.map (Json.str ·.toString))),
    ("theorems", r.theorems), ("with_relation", r.withRelation), ("no_relation", r.theorems - r.withRelation - r.failed),
    ("fully_covered", r.full), ("covered_up_to_uninterpreted", r.upToUninterpreted), ("failed", r.failed),
    ("opaque_heads", Json.arr (r.heads.map fun (h, c, ex) =>
      Json.mkObj [("head", h.toString), ("statements", c), ("example", ex.toString)]))]

/-- The human summary: counts, shares and the top opaque heads. -/
def Report.summary (r : Report) : String :=
  let heads := (r.heads.toList.take topHeads).map fun (h, c, ex) => s!"  {c}  {h}  (e.g. {ex})"
  "\n".intercalate ([
    s!"theorems: {r.theorems}, with a relation: {r.withRelation}, failed: {r.failed}",
    s!"fully covered: {r.full} ({percent r.full r.withRelation})",
    s!"covered up to uninterpreted functions: {r.upToUninterpreted} ({percent r.upToUninterpreted r.withRelation})",
    "opaque heads:"] ++ heads)

/-- Measure the corpus: one verdict per theorem, a failure (timeout, elaboration error) counted, never fatal. -/
def measure (prefixes : Array Name) : MetaM Report := do
  let thms := corpus (← getEnv) prefixes
  let mut verdicts := #[]
  let mut failed := 0
  for (n, type) in thms do
    try
      let acc ← withCurrHeartbeats (statementAcc type)
      verdicts := verdicts.push (judge n acc)
    catch _ =>
      failed := failed + 1
  return aggregate prefixes thms.size failed verdicts

/-- `#veriphy_coverage [Prefix, …]` measures the translation's coverage of a corpus; see the module doc. -/
syntax (name := veriphyCoverage) "#veriphy_coverage " "[" ident,* "]" (str)? : command

elab_rules : command
  | `(#veriphy_coverage [$ps,*] $[$out]?) => do
    let prefixes := ps.getElems.map (·.getId)
    let report ← liftTermElabM (measure prefixes)
    logInfo report.summary
    unless veriphy.coverage.write.get (← getOptions) do return
    let file ← match out with
      | some s => pure (System.FilePath.mk s.getString)
      | none => do
        let stem := "_".intercalate (prefixes.toList.map toString)
        pure ((← projectDir) / "coverage" / s!"{stem}.json")
    if let some dir := file.parent then IO.FS.createDirAll dir
    IO.FS.writeFile file (report.toJson.pretty ++ "\n")
    logInfo m!"report written to {file}"

end Veriphy.Coverage
