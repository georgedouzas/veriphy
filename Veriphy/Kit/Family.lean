/-
Close a goal with a tactic block and emit it as the `Sage-free replacement:`.

`closeAndEmit` runs exactly the syntax it prints ("run what you print"), fails if
any error is logged (even inside a nested `by`), rejects proofs that use `sorry`
or any axiom beyond `propext`, `Classical.choice` and `Quot.sound`, replays the
printed text when `veriphy.checkReplay` is set, and attaches one suggestion.
-/
import Mathlib.Tactic.LinearCombination
import Mathlib.Tactic.NormNum
import Mathlib.Tactic.Positivity
import Mathlib.Tactic.Ring
import Veriphy.Kit.Replay

namespace Veriphy

open Lean Elab Tactic Meta

/-- The axioms a Veriphy proof may depend on: Lean's standard three. -/
def standardAxioms : List Name := [``propext, ``Classical.choice, ``Quot.sound]

/-- Reject a proof of `goal` that uses `sorry` or depends on an axiom outside `standardAxioms`
(such as `Lean.ofReduceBool`, which `native_decide` introduces). Unassigned subgoals are allowed. -/
def checkAxioms (goal : MVarId) : MetaM Unit := do
  let proof ← instantiateMVars (mkMVar goal)
  if proof.hasSorry then
    throwError "veriphy: the proof uses `sorry` (sorryAx); only fully checked proofs are accepted"
  let mut checked : NameSet := {}
  for c in proof.getUsedConstants do
    for ax in ← collectAxioms c do
      if checked.contains ax then continue
      checked := checked.insert ax
      unless standardAxioms.contains ax do
        throwError "veriphy: the proof depends on the axiom `{ax}`; only `propext`, `Classical.choice` and \
          `Quot.sound` are accepted"

/-- Run `proof` on the main goal, replay it if `veriphy.checkReplay` is set, and emit it as the single
`Sage-free replacement:` for the whole current tactic (`getRef`, so applying it also replaces the
tactic's arguments). On failure the state is restored and nothing is emitted. -/
def closeAndEmit (proof : TSyntax `tactic) : TacticM Unit := do
  let s₀ ← saveState
  let goal ← getMainGoal
  let errors := fun (log : MessageLog) =>
    log.reportedPlusUnreported.toList.filter (·.severity == .error)
  let before := (errors (← Core.getMessageLog)).length
  try
    -- no error recovery: a checker failing inside a nested `by` must fail the tactic, not be logged
    Term.withoutErrToSorry <| withoutRecover <| evalTactic proof
    let logged := (errors (← Core.getMessageLog)).drop before
    unless logged.isEmpty do
      -- the restore below drops these from the log, so they travel in this error instead
      let texts ← logged.mapM fun m => m.data.toString
      throwError "veriphy: the certificate check failed:\n{"\n".intercalate texts}"
    checkAxioms goal
  catch ex =>
    s₀.restore
    throw ex
  if veriphy.checkReplay.get (← getOptions) then
    replay s₀ proof (← getUnsolvedGoals)
  Lean.Meta.Tactic.TryThis.addSuggestion (← getRef) proof (header := "Sage-free replacement: ")


end Veriphy
