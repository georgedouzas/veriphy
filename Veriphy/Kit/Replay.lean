/-
Replay check and the guarded daemon entry point.

`set_option veriphy.checkReplay true` makes every replacement emitted through a
checker family prove itself the way a user would use it: pretty-printed to text,
re-parsed, and re-run on the original goal with the Sage bridge disabled. A
hygienic name (`h✝`), a printer quirk, or a hidden Sage call fails the tactic
with the printed text in the message.
-/
import Lean
import Veriphy.Bridge

namespace Veriphy

open Lean Elab Tactic Meta

register_option veriphy.checkReplay : Bool := {
  defValue := false
  descr := "Veriphy: re-parse and re-run every emitted `Try this:` replacement on the original goal, \
    with the Sage bridge disabled (used by the test suite)"
}

register_option veriphy.internal.replaying : Bool := {
  defValue := false
  descr := "Veriphy (internal): set while a replacement is being replayed; the Sage bridge refuses requests"
}

namespace Kit

/-- Fail if the bridge is disabled (we are replaying an emitted replacement). -/
def guardBridge (what : String) : CoreM Unit := do
  if veriphy.internal.replaying.get (← getOptions) then
    throwError "veriphy: the Sage bridge is disabled during replay, but the replacement called \
      Sage ({what}); a committed proof must not need Sage"

/-- Run a daemon request (a `Bridge` call) from a tactic. Tactics reach Sage only through here. -/
def run {α : Type} (what : String) (x : IO α) : CoreM α := do
  guardBridge what
  x

end Kit

/-- Replay `proof` from the state `s₀` (before it ran) and check it leaves the goals `after` left.
Leaves the current state untouched. -/
def replay (s₀ : Tactic.SavedState) (proof : TSyntax `tactic) (after : List MVarId) : TacticM Unit := do
  let text := toString (← PrettyPrinter.ppTactic proof)
  let stx ← match Parser.runParserCategory (← getEnv) `tactic text with
    | .ok stx => pure stx
    | .error e => throwError "veriphy replay: the printed replacement does not re-parse ({e}):\n{text}"
  let expected ← after.mapM fun g => do instantiateMVars (← g.getType)
  let s₁ ← saveState
  let result ← try
      s₀.restore
      withOptions (veriphy.internal.replaying.set · true) (evalTactic stx)
      let got ← (← getUnsolvedGoals).mapM fun g => do instantiateMVars (← g.getType)
      if got.length != expected.length then
        pure (some m!"it leaves {got.length} goal(s), the tactic left {expected.length}:\
          {MessageData.joinSep (got.map indentExpr) ""}")
      else
        let mut bad := none
        for (g, e) in got.zip expected do
          unless ← isDefEq g e do
            bad := some m!"it leaves the goal{indentExpr g}\ninstead of{indentExpr e}"
            break
        pure bad
    catch ex => pure (some m!"it fails: {ex.toMessageData}")
  s₁.restore (restoreInfo := true)
  if let some why := result then
    throwError "veriphy replay: the printed replacement does not reproduce the proof — {why}\n\
      replacement:\n{text}"

end Veriphy
