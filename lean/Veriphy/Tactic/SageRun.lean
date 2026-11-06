/-
`sage_run`: close a goal with whatever proof a Sage script builds.

The goal and every nameable hypothesis are extracted (leniently: anything without
a polynomial form is passed as text) and bound in the script as `problem`, next
to the `veriphy.toolkit` emitters and solvers. The script assigns `proof`, a Lean
tactic block. Lean parses and runs that block; the kernel decides. The block is
emitted as the `Sage-free replacement:` — the script never reaches the committed
proof. Scripts live in the caller's project, under `.veriphy/certificates/`.
-/
import Mathlib.Tactic.FieldSimp
import Mathlib.Tactic.Linarith
import Veriphy.Kit

namespace Veriphy

open Lean Elab Tactic Meta

/-- One error with the script's output, the Lean text it built, and what went wrong with it. -/
private def combined (what : MessageData) (stdout lean : String) : MessageData :=
  let section_ (title body : String) : MessageData :=
    if body.trim.isEmpty then m!"" else m!"\n── {title} ──\n{body.trimRight}"
  m!"sage_run: {what}{section_ "script output" stdout}{section_ "Lean text" lean}"

/-- Run `script` on the main goal: build the problem, ask Sage for the proof block, then check and emit it. -/
def sageRunCore (script : String) : TacticM Unit := do
  let (lean, stdout, leavesGoals) ← withLenientProblem fun p => do
    let problem ← p.toJson
    Kit.run "run" (Bridge.run problem script)
  -- one tactic sequence: `(t₁ ⏎ t₂ …)`, every line shifted one column to sit inside the parentheses
  let block := "(" ++ "\n ".intercalate (lean.splitOn "\n") ++ ")"
  let stx ← match Parser.runParserCategory (← getEnv) `tactic block "<sage_run>" with
    | .ok stx => pure stx
    | .error e => throwError combined m!"the script's proof does not parse: {e}" stdout lean
  try
    -- inside `veriphy_certified`, so the proof term records that a recipe built it (`#veriphy_levels`)
    closeAndEmit (← `(tactic| veriphy_certified $(⟨stx⟩))) (leavesGoals := leavesGoals)
  catch ex =>
    throwError combined m!"the script's proof does not close the goal:\n{ex.toMessageData}" stdout lean

/-- `sage_run "<sage script>"` — run a proof script against the goal; see the module doc. -/
syntax (name := sageRun) "sage_run " str : tactic

/-- `sage_run file "<name>.sage"` — run a saved proof script from the project's `.veriphy/certificates/`. -/
syntax (name := sageRunFile) "sage_run " &"file " str : tactic

elab_rules : tactic
  | `(tactic| sage_run $s:str) => sageRunCore s.getString
  | `(tactic| sage_run file $p:str) => do sageRunCore (← readScript p.getString)

end Veriphy
