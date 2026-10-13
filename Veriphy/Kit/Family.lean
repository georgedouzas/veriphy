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

/-- The most `first` combinators a block may hold for its replacement to be minimized (each one costs reruns). -/
def maxFirstNodes : Nat := 8

/-- The `first` combinators of a tactic block, outermost first. -/
partial def firstNodes (stx : Syntax) : Array Syntax :=
  match stx with
  | .node _ kind args =>
    let inner := args.foldl (init := #[]) fun acc a => acc ++ firstNodes a
    if kind == ``Lean.Parser.Tactic.first then #[stx] ++ inner else inner
  | _ => #[]

/-- Do two syntax nodes come from the same source range? -/
private def sameRange (a b : Syntax) : Bool :=
  a.getPos?.isSome && a.getPos? == b.getPos? && a.getTailPos? == b.getTailPos?

/-- Replace the node with the same source range as `target` by `replacement`; `none` when it is not there. -/
partial def replaceNode (stx target replacement : Syntax) : Option Syntax :=
  if sameRange stx target then some replacement else
  match stx with
  | .node info kind args => Id.run do
    for h : i in [0:args.size] do
      if let some a := replaceNode args[i] target replacement then
        return some (.node info kind (args.set i a))
    return none
  | _ => none

/-- Does the block, run from `s₀`, close what the original closed: no error, and as many goals left? -/
private def runsLike (s₀ : Tactic.SavedState) (block : Syntax) (goalsLeft : Nat) : TacticM Bool := do
  s₀.restore
  try
    let errorsBefore := (← Core.getMessageLog).reportedPlusUnreported.size
    Term.withoutErrToSorry <| withoutRecover <| evalTactic block
    let clean := (← Core.getMessageLog).reportedPlusUnreported.size == errorsBefore
    return clean && (← getUnsolvedGoals).length == goalsLeft
  catch _ => return false

/-- Replace each `first | t₁ | t₂ …` by its first alternative with which the whole block still succeeds, so the
replacement shows what ran rather than every fallback. A `first` whose goals need different alternatives (under
`<;>`, say) is kept. The state after the original run is restored. -/
def keepRunAlternatives (s₀ : Tactic.SavedState) (proof : Syntax) : TacticM Syntax := do
  let nodes := firstNodes proof
  if nodes.isEmpty || nodes.size > maxFirstNodes then return proof
  let s₁ ← saveState
  let goalsLeft := (← getUnsolvedGoals).length
  let mut current := proof
  for node in nodes do
    for alternative in (node[1].getArgs.map (·[1])) do
      -- a single tactic stands on its own; a sequence is parenthesized
      let tactics := alternative[0][0].getSepArgs
      let wrapped ← if h : tactics.size = 1 then pure tactics[0] else `(tactic| ($(⟨alternative⟩)))
      let some candidate := replaceNode current node wrapped | break
      if ← runsLike s₀ candidate goalsLeft then
        current := candidate
        break
  s₁.restore
  return current

/-- Run `proof` on the main goal, replay it if `veriphy.checkReplay` is set, and emit what ran as the single
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
  -- emit what ran: a `first | …` becomes the alternative that closed its goal (the replay checks the result)
  let proof : TSyntax `tactic := ⟨← keepRunAlternatives s₀ proof⟩
  if veriphy.checkReplay.get (← getOptions) then
    replay s₀ proof (← getUnsolvedGoals)
  Lean.Meta.Tactic.TryThis.addSuggestion (← getRef) proof (header := "Sage-free replacement: ")


end Veriphy
