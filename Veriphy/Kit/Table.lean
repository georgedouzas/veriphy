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

/-- A domain condition an entry imposes. `ne`, `nonneg` and `pos` constrain one argument (`arg`), `ne` against
`rhs` when given (`b ≠ 1`) and against zero otherwise; `le` says `lhs ≤ rhs`. Sides are arguments (`#i`) or
integer numerals. -/
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
  /-- The conditions under which Lean's derivative of the function agrees with the calculus one, when they differ
  from `conditions` (`Real.log` is differentiable away from `0`, `Real.sqrt` only where it is positive). -/
  derivConditions : Option (List CondSpec) := none
  deriving ToJson, FromJson, BEq, Repr, Inhabited

/-- A constant such as `Real.pi`, written `sage` in Sage. -/
structure ConstantEntry where
  lean : String
  sage : String
  type : String
  deriving ToJson, FromJson, BEq, Repr, Inhabited

/-- A rewrite by a named lemma. It applies to goals that mention all of `functions` (Lean constants); `pattern`, a
Sage expression with wildcards `w0`, `w1`, …, binds the lemma's arguments in the goal's symbolic form, and the side
conditions are Lean text in which `#i` stands for the argument bound to `wi`. `example` is a worked goal. -/
structure RewriteEntry where
  «lemma» : String
  functions : List String
  reverse : Bool := false
  side : List String := []
  «example» : String := ""
  pattern : Option String := none
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
    { unary "Real.sqrt" "sqrt" "ℝ" [{ kind := "nonneg", arg := some 0 }] with
      derivConditions := some [{ kind := "pos", arg := some 0 }] },
    unary "Real.exp" "exp" "ℝ",
    { unary "Real.log" "log" "ℝ" [{ kind := "pos", arg := some 0 }] with
      derivConditions := some [{ kind := "ne", arg := some 0 }] },
    unary "Real.sin" "sin" "ℝ", unary "Real.cos" "cos" "ℝ", unary "Real.tan" "tan" "ℝ",
    unary "Real.cosh" "cosh" "ℝ", unary "Real.sinh" "sinh" "ℝ", unary "Real.tanh" "tanh" "ℝ",
    unary "Real.arctan" "arctan" "ℝ",
    unary "Real.arcsin" "arcsin" "ℝ" [{ kind := "le", lhs := some "-1", rhs := some "#0" },
      { kind := "le", lhs := some "#0", rhs := some "1" }],
    unary "Real.arccos" "arccos" "ℝ" [{ kind := "le", lhs := some "-1", rhs := some "#0" },
      { kind := "le", lhs := some "#0", rhs := some "1" }],
    { lean := "Real.logb", sage := "logb", arity := 2, types := ["ℝ"], result := "ℝ",
      conditions := [{ kind := "pos", arg := some 0 }, { kind := "ne", arg := some 0, rhs := some "1" },
        { kind := "pos", arg := some 1 }],
      «example» := "Real.logb b x" },
    { lean := "Nat.factorial", sage := "factorial", arity := 1, types := ["ℕ"], result := "ℕ",
      «example» := "Nat.factorial n" },
    { lean := "Nat.choose", sage := "binomial", arity := 2, types := ["ℕ"], result := "ℕ",
      «example» := "Nat.choose n k" },
    { lean := "Nat.gcd", sage := "gcd", arity := 2, types := ["ℕ"], result := "ℕ", «example» := "Nat.gcd m n" },
    { lean := "Int.gcd", sage := "gcd", arity := 2, types := ["ℤ"], result := "ℕ", «example» := "Int.gcd a b" },
    { lean := "Int.floor", sage := "floor", arity := 1, types := ["ℝ", "ℚ"], result := "ℤ", «example» := "⌊x⌋" },
    { lean := "Int.ceil", sage := "ceil", arity := 1, types := ["ℝ", "ℚ"], result := "ℤ", «example» := "⌈x⌉" },
    -- a linear order's `max` and `min`; Sage's `max_symbolic` and `min_symbolic`, bound to these names
    { lean := "Max.max", sage := "max", arity := 2, «example» := "max x y" },
    { lean := "Min.min", sage := "min", arity := 2, «example» := "min x y" },
    unary "Complex.exp" "exp" "ℂ", unary "Complex.log" "log" "ℂ",
    unary "Complex.sin" "sin" "ℂ", unary "Complex.cos" "cos" "ℂ", unary "Complex.tan" "tan" "ℂ"]
  constants := [
    { lean := "Real.pi", sage := "pi", type := "ℝ" },
    { lean := "Complex.I", sage := "I", type := "ℂ" }]
  coercions := ["Nat.cast", "Int.cast", "Rat.cast", "Complex.ofReal", "Fin.val"]
  rewrites := [
    { «lemma» := "Real.exp_add", functions := ["Real.exp"], reverse := true,
      «example» := "Real.exp a * Real.exp b = Real.exp (a + b)" },
    { «lemma» := "Real.sin_sq_add_cos_sq", functions := ["Real.sin", "Real.cos"],
      «example» := "Real.sin x ^ 2 + Real.cos x ^ 2 = 1" },
    { «lemma» := "Real.cos_sq_add_sin_sq", functions := ["Real.cos", "Real.sin"],
      «example» := "Real.cos x ^ 2 + Real.sin x ^ 2 = 1" },
    { «lemma» := "Real.cos_sq", functions := ["Real.cos"], pattern := some "cos(w0)^2",
      «example» := "Real.cos x ^ 2 = 1 / 2 + Real.cos (2 * x) / 2" },
    { «lemma» := "Real.sin_sq_eq_half_sub", functions := ["Real.sin"], pattern := some "sin(w0)^2",
      «example» := "Real.sin x ^ 2 = 1 / 2 - Real.cos (2 * x) / 2" },
    { «lemma» := "Real.sin_two_mul", functions := ["Real.sin"], pattern := some "sin(2*w0)",
      «example» := "Real.sin (2 * x) = 2 * Real.sin x * Real.cos x" },
    { «lemma» := "Real.cos_two_mul", functions := ["Real.cos"], pattern := some "cos(2*w0)",
      «example» := "Real.cos (2 * x) = 2 * Real.cos x ^ 2 - 1" },
    { «lemma» := "Real.sin_three_mul", functions := ["Real.sin"], pattern := some "sin(3*w0)",
      «example» := "Real.sin (3 * x) = 3 * Real.sin x - 4 * Real.sin x ^ 3" },
    { «lemma» := "Real.cos_three_mul", functions := ["Real.cos"], pattern := some "cos(3*w0)",
      «example» := "Real.cos (3 * x) = 4 * Real.cos x ^ 3 - 3 * Real.cos x" },
    { «lemma» := "Real.cosh_sq", functions := ["Real.cosh", "Real.sinh"],
      «example» := "Real.cosh x ^ 2 = Real.sinh x ^ 2 + 1" },
    { «lemma» := "Real.log_div", functions := ["Real.log"], pattern := some "log(w0*w1^(-1))",
      side := ["#0 ≠ 0", "#1 ≠ 0"], «example» := "Real.log (x / y) = Real.log x - Real.log y" },
    { «lemma» := "Real.log_mul", functions := ["Real.log"], pattern := some "log(w0*w1)",
      side := ["#0 ≠ 0", "#1 ≠ 0"], «example» := "Real.log (x * y) = Real.log x + Real.log y" },
    { «lemma» := "Real.log_rpow", functions := ["Real.log"], pattern := some "log(w0^w1)",
      side := ["0 < #0"], «example» := "Real.log (x ^ y) = y * Real.log x" },
    { «lemma» := "Real.exp_log", functions := ["Real.exp", "Real.log"], side := ["0 < x"],
      «example» := "Real.exp (Real.log x) = x" },
    { «lemma» := "Real.log_exp", functions := ["Real.log", "Real.exp"],
      «example» := "Real.log (Real.exp x) = x" },
    { «lemma» := "Real.sqrt_mul_self", functions := ["Real.sqrt"], side := ["0 ≤ a"],
      «example» := "Real.sqrt a * Real.sqrt a = a" }]

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
