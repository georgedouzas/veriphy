/-
The library packs Veriphy ships, and the tables in force for the current environment.

`#veriphy_tables` prints the active namespaces (core, packs whose library is imported, project), their entry counts
and any problem found while resolving them (missing constants, conflicts).
-/
import Veriphy.Kit.Table

namespace Veriphy

open Lean Elab Command

/-- The library packs shipped with Veriphy (data only; none of their libraries is imported). -/
def shippedPacks : List Pack := []

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
