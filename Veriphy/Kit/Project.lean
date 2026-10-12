/-
The downstream project's Veriphy directory: everything Veriphy reads or writes in a project lives under
`.veriphy/` at the Lean workspace root (`certificates/`, `translations/`, `lean/`, `coverage/`).
-/

namespace Veriphy

open System

/-- The name of the project directory holding every Veriphy artifact. -/
def projectDirName : String := ".veriphy"

/-- Does `dir` hold a Lake workspace's root lakefile? -/
private def hasLakefile (dir : FilePath) : IO Bool := do
  return (← (dir / "lakefile.toml").pathExists) || (← (dir / "lakefile.lean").pathExists)

/-- The Lean workspace root: the nearest directory, from `start` upwards, holding a lakefile, else `start`. -/
partial def workspaceRoot (start : Option FilePath := none) : IO FilePath := do
  let start ← match start with | some d => pure d | none => IO.currentDir
  let rec go (dir : FilePath) : IO FilePath := do
    if ← hasLakefile dir then return dir
    match dir.parent with
    | some parent => if parent == dir then return start else go parent
    | none => return start
  go start

/-- The project's `.veriphy/` directory (not created: writers create what they need). -/
def projectDir (start : Option FilePath := none) : IO FilePath :=
  return (← workspaceRoot start) / projectDirName

/-- Resolve a `sage_run file` path: a bare file name lives in `.veriphy/certificates/`, any other relative path
is taken from the workspace root, and an absolute path is kept. -/
def resolveScriptPath (path : String) (start : Option FilePath := none) : IO FilePath := do
  let p : FilePath := path
  if p.isAbsolute then return p
  if p.components.length == 1 then return (← projectDir start) / "certificates" / path
  return (← workspaceRoot start) / p

/-- Resolve a script path (a bare name in `.veriphy/certificates/`, otherwise from the workspace root) and read it. -/
def readScript (path : String) : IO String := do
  let resolved ← resolveScriptPath path
  unless ← resolved.pathExists do
    throw <| IO.userError s!"sage_run: no script at '{resolved}'"
  IO.FS.readFile resolved

end Veriphy
