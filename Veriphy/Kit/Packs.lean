/-
The library packs Veriphy ships, and the tables in force for the current environment.

`#veriphy_tables` prints the active namespaces (core, packs whose library is imported, project), their entry counts
and any problem found while resolving them (missing constants, conflicts).
-/
import Veriphy.Kit.Table
import Veriphy.Kit.Project
import Veriphy.Packs.Physlib

namespace Veriphy

open Lean Elab Command

/-- The library packs shipped with Veriphy (data only; none of their libraries is imported). -/
def shippedPacks : List Pack := [Packs.physlib]

/-- The tables in force in the current environment, with the problems found resolving them. -/
def activeTables (project : List Table := []) : CoreM (Tables × Array String) :=
  return resolveTables (← getEnv) shippedPacks project

/-- One line per table: its namespace and how many entries of each kind it has. -/
def describeTables (ts : Tables) : List String :=
  ts.map fun t => s!"{t.«namespace»}: {t.functions.length} functions, {t.constants.length} constants, " ++
    s!"{t.coercions.length} coercions, {t.rewrites.length} rewrites"

/-- `#veriphy_tables` — the translation tables in force here. -/
syntax (name := veriphyTables) "#veriphy_tables" : command

elab_rules : command
  | `(#veriphy_tables) => do
    let (ts, problems) ← liftCoreM (activeTables)
    logInfo ("\n".intercalate (describeTables ts ++ problems.toList.map ("problem: " ++ ·)))

end Veriphy

namespace Veriphy

open Lean

/-! ## Project tables: `.veriphy/translations/*.json` -/

/-- A required string field. -/
private def textField (file : String) (j : Json) (key : String) : Except String String :=
  match j.getObjVal? key with
  | .ok (.str s) => .ok s
  | .ok _ => .error s!"{file}: field '{key}' must be a string"
  | .error _ => .error s!"{file}: missing field '{key}'"

/-- An optional field, parsed by `parse` when present. -/
private def optionalField {α} (j : Json) (key : String) (dflt : α) (parse : Json → Except String α) :
    Except String α :=
  match j.getObjVal? key with
  | .ok .null | .error _ => .ok dflt
  | .ok v => parse v

/-- A list of strings. -/
private def stringList (file key : String) (v : Json) : Except String (List String) := do
  let .arr items := v | .error s!"{file}: field '{key}' must be a list of strings"
  items.toList.mapM fun
    | .str s => .ok s
    | _ => .error s!"{file}: field '{key}' must be a list of strings"

/-- A list of objects, each parsed by `parse`. -/
private def objectList {α} (file key : String) (parse : Json → Except String α) (v : Json) : Except String (List α) := do
  let .arr items := v | .error s!"{file}: field '{key}' must be a list of objects"
  items.toList.mapM parse

private def parseCondition (file : String) (j : Json) : Except String CondSpec := do
  let kind ← textField file j "kind"
  unless ["ne", "nonneg", "pos", "le"].contains kind do
    .error s!"{file}: field 'kind' must be one of ne, nonneg, pos, le, got '{kind}'"
  let arg ← optionalField j "arg" none fun v => match v.getNat? with
    | .ok n => .ok (some n)
    | .error _ => .error s!"{file}: field 'arg' must be a natural number"
  let side (k : String) := optionalField j k none fun v => match v with
    | .str s => .ok (some s)
    | _ => .error s!"{file}: field '{k}' must be a string"
  return { kind, arg, lhs := ← side "lhs", rhs := ← side "rhs" }

private def parseFunction (file : String) (j : Json) : Except String FunctionEntry := do
  let arity ← match j.getObjVal? "arity" with
    | .ok v => match v.getNat? with
      | .ok n => .ok n
      | .error _ => .error s!"{file}: field 'arity' must be a natural number"
    | .error _ => .error s!"{file}: missing field 'arity'"
  let role ← optionalField j "role" none fun
    | .str s => if ["derivative", "partial"].contains s then .ok (some s)
        else .error s!"{file}: field 'role' must be derivative or partial, got '{s}'"
    | _ => .error s!"{file}: field 'role' must be a string"
  return {
    lean := ← textField file j "lean", sage := ← textField file j "sage", arity,
    types := ← optionalField j "types" [] (stringList file "types"),
    result := ← optionalField j "result" "" fun v => match v with
      | .str s => .ok s
      | _ => .error s!"{file}: field 'result' must be a string",
    conditions := ← optionalField j "conditions" [] (objectList file "conditions" (parseCondition file)),
    «example» := ← optionalField j "example" "" fun v => match v with
      | .str s => .ok s
      | _ => .error s!"{file}: field 'example' must be a string",
    role }

private def parseRewrite (file : String) (j : Json) : Except String RewriteEntry := do
  let functions ← match j.getObjVal? "functions" with
    | .ok v => stringList file "functions" v
    | .error _ => .error s!"{file}: missing field 'functions'"
  return {
    «lemma» := ← textField file j "lemma", functions,
    reverse := ← optionalField j "reverse" false fun v => match v.getBool? with
      | .ok b => .ok b
      | .error _ => .error s!"{file}: field 'reverse' must be true or false",
    side := ← optionalField j "side" [] (stringList file "side"),
    «example» := ← optionalField j "example" "" fun v => match v with
      | .str s => .ok s
      | _ => .error s!"{file}: field 'example' must be a string",
    pattern := ← optionalField j "pattern" none fun v => match v with
      | .str s => .ok (some s)
      | _ => .error s!"{file}: field 'pattern' must be a string" }

private def parseConstant (file : String) (j : Json) : Except String ConstantEntry := do
  return { lean := ← textField file j "lean", sage := ← textField file j "sage", type := ← textField file j "type" }

/-- Parse one project file into a table of the `project` namespace, naming the file and field on any error. -/
def parseProjectTable (file : String) (j : Json) : Except String Table := do
  unless j matches .obj _ do .error s!"{file}: must be a JSON object"
  return {
    «namespace» := "project",
    functions := ← optionalField j "functions" [] (objectList file "functions" (parseFunction file)),
    constants := ← optionalField j "constants" [] (objectList file "constants" (parseConstant file)),
    coercions := ← optionalField j "coercions" [] (stringList file "coercions"),
    rewrites := ← optionalField j "rewrites" [] (objectList file "rewrites" (parseRewrite file)) }

/-- Load the project's tables from a directory of JSON files: the tables that parsed, and an error for each file
that did not (it is skipped, the others still load). -/
def loadProjectTables (dir : System.FilePath) : IO (List Table × Array String) := do
  unless ← dir.isDir do return ([], #[])
  let files := (← dir.readDir).filter (·.path.extension == some "json") |>.qsort (·.fileName < ·.fileName)
  let mut tables := []
  let mut problems := #[]
  for f in files do
    let name := s!"{System.FilePath.mk "translations" / f.fileName}"
    let text ← IO.FS.readFile f.path
    let parsed : Except String Table := do
      let j ← (Json.parse text).mapError (s!"{name}: not valid JSON: " ++ ·)
      parseProjectTable name j
    match parsed with
    | .ok t => tables := tables ++ [t]
    | .error e => problems := problems.push e
  return (tables, problems)

/-- The project tables, cached per Lean process by the files' modification times. -/
initialize projectTableCache : IO.Ref (Option (List (String × Nat) × List Table × Array String)) ← IO.mkRef none

/-- The project's tables from `.veriphy/translations/`, reloaded only when a file changed. -/
def projectTables : IO (List Table × Array String) := do
  let dir := (← projectDir) / "translations"
  let stamps ← if ← dir.isDir then
      (← dir.readDir).toList.mapM fun f => return (f.fileName, (← f.path.metadata).modified.sec.toNat)
    else pure []
  if let some (cached, tables, problems) := ← projectTableCache.get then
    if cached == stamps then return (tables, problems)
  let (tables, problems) ← loadProjectTables dir
  projectTableCache.set (some (stamps, tables, problems))
  return (tables, problems)

end Veriphy
