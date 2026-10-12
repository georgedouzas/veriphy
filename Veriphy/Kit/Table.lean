/-
Translation tables as data. One schema serves the core (`mathlib` namespace), library packs and the project's
`.veriphy/translations/`; the Python toolkit reads the same records from `veriphy/toolkit/core_table.json`, and a
Sage-free test keeps the two copies of the core equal.

The function and constant entries follow LeanSage's `ExprToAST.lean` (Oliver Dressler, MIT License,
https://github.com/oOo0oOo/LeanSage), restricted to Veriphy's coverage list.
-/
import Lean

namespace Veriphy

open Lean

/-- A domain condition an entry imposes. `ne`, `nonneg` and `pos` constrain one argument (`arg`); `le` says
`lhs ≤ rhs`, each side an argument (`#i`) or a numeral. -/
structure CondSpec where
  kind : String
  arg : Option Nat := none
  lhs : Option String := none
  rhs : Option String := none
  deriving ToJson, FromJson, BEq, Repr, Inhabited

/-- A function: the Lean constant applied to its last `arity` arguments, written `sage(…)` in Sage. `types` lists
the argument types it applies to (empty: any), `example` is a Lean term over variables for the round-trip check.
`role` is `none` for an ordinary function, `derivative` for a derivative applied as `(f, point)`, and `partial` for
a partial derivative applied as `(coordinate, f, point)`. -/
structure FunctionEntry where
  lean : String
  sage : String
  arity : Nat
  types : List String := []
  result : String := ""
  conditions : List CondSpec := []
  «example» : String := ""
  role : Option String := none
  deriving ToJson, FromJson, BEq, Repr, Inhabited

/-- A constant such as `Real.pi`, written `sage` in Sage. -/
structure ConstantEntry where
  lean : String
  sage : String
  type : String
  deriving ToJson, FromJson, BEq, Repr, Inhabited

/-- A rewrite by a named lemma: the functions it applies to, its direction, its side conditions (Lean text over the
goal's atoms, filled in by the script) and a worked example goal. -/
structure RewriteEntry where
  «lemma» : String
  functions : List String
  reverse : Bool := false
  side : List String := []
  «example» : String := ""
  deriving ToJson, FromJson, BEq, Repr, Inhabited

/-- A convention a namespace fixes, such as the metric signature. -/
structure Convention where
  key : String
  value : String
  deriving ToJson, FromJson, BEq, Repr, Inhabited

/-- One namespace's entries. -/
structure Table where
  «namespace» : String
  functions : List FunctionEntry := []
  constants : List ConstantEntry := []
  coercions : List String := []
  rewrites : List RewriteEntry := []
  conventions : Option (List Convention) := none
  deriving ToJson, FromJson, BEq, Repr, Inhabited

private def unary (lean sage ty : String) (conditions : List CondSpec := []) : FunctionEntry :=
  { lean, sage, arity := 1, types := [ty], result := ty, conditions,
    «example» := s!"{lean} x" }

/-- The core table: the `mathlib` namespace. -/
def coreTable : Table where
  «namespace» := "mathlib"
  functions := [
    unary "Real.sqrt" "sqrt" "ℝ" [{ kind := "nonneg", arg := some 0 }],
    unary "Real.exp" "exp" "ℝ",
    unary "Real.log" "log" "ℝ" [{ kind := "pos", arg := some 0 }],
    unary "Real.sin" "sin" "ℝ", unary "Real.cos" "cos" "ℝ", unary "Real.tan" "tan" "ℝ",
    unary "Complex.exp" "exp" "ℂ", unary "Complex.log" "log" "ℂ",
    unary "Complex.sin" "sin" "ℂ", unary "Complex.cos" "cos" "ℂ", unary "Complex.tan" "tan" "ℂ"]
  constants := [
    { lean := "Real.pi", sage := "pi", type := "ℝ" },
    { lean := "Complex.I", sage := "I", type := "ℂ" }]
  coercions := ["Nat.cast", "Int.cast", "Rat.cast", "Complex.ofReal"]

/-- The tables in force, in resolution order (core first). -/
abbrev Tables := List Table

/-- The function entry for a Lean constant, from the first table that has one. -/
def Tables.function? (ts : Tables) (c : Name) : Option FunctionEntry :=
  ts.findSome? fun t => t.functions.find? (·.lean == c.toString)

/-- The constant entry for a Lean constant. -/
def Tables.constant? (ts : Tables) (c : Name) : Option ConstantEntry :=
  ts.findSome? fun t => t.constants.find? (·.lean == c.toString)

/-- Is the Lean constant a coercion translated as its argument? -/
def Tables.isCoercion (ts : Tables) (c : Name) : Bool :=
  ts.any fun t => t.coercions.contains c.toString

end Veriphy

namespace Veriphy

open Lean

/-- A library pack: a table for one library, shipped with Veriphy as data and active only when the library is in
the environment (its sentinel constant exists). Veriphy never imports the library itself. -/
structure Pack where
  /-- The library, such as `Physlib`. -/
  library : String
  /-- A constant whose presence means the library is imported. -/
  sentinel : String
  table : Table
  deriving Inhabited

/-- Every Lean constant an entry refers to. -/
def Table.referencedConstants (t : Table) : List String :=
  t.functions.map (·.lean) ++ t.constants.map (·.lean) ++ t.coercions ++ t.rewrites.map (·.«lemma»)

/-- The Lean constants a table defines translations for (functions, constants, coercions). -/
def Table.definedConstants (t : Table) : List String :=
  t.functions.map (·.lean) ++ t.constants.map (·.lean) ++ t.coercions

/-- Drop the entries of `t` that redefine a constant an earlier table defines, reporting each conflict. -/
def Table.withoutConflicts (t : Table) (earlier : Tables) : Table × Array String := Id.run do
  let owner? (c : String) : Option String := (earlier.find? (·.definedConstants.contains c)).map (·.«namespace»)
  let conflict (c ns : String) : String :=
    s!"{t.«namespace»}: entry for {c} conflicts with the {ns} entry for {c}; the {ns} entry stays"
  let mut problems := #[]
  let mut functions := []
  for f in t.functions do
    if let some ns := owner? f.lean then problems := problems.push (conflict f.lean ns)
    else functions := functions ++ [f]
  let mut constants := []
  for c in t.constants do
    if let some ns := owner? c.lean then problems := problems.push (conflict c.lean ns)
    else constants := constants ++ [c]
  return ({ t with functions, constants }, problems)

/-- Resolve the tables in force: the core, then each pack whose library is present (in name order), then the
project's tables. Returns the tables and the problems found (missing constants, conflicts). -/
def resolveTables (env : Environment) (packs : List Pack) (project : List Table := []) : Tables × Array String :=
  Id.run do
  let mut tables : Tables := [coreTable]
  let mut problems := #[]
  let active := packs.filter (env.contains ·.sentinel.toName) |>.mergeSort (·.library ≤ ·.library)
  for t in active.map (·.table) ++ project do
    let missing := t.referencedConstants.filter (!env.contains ·.toName)
    unless missing.isEmpty do
      problems := problems.push
        s!"{t.«namespace»}: constants not found (library version mismatch?): {", ".intercalate missing}"
    let (t, conflicts) := t.withoutConflicts tables
    problems := problems ++ conflicts
    tables := tables ++ [t]
  return (tables, problems)

end Veriphy
