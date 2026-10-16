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

/-- Are two syntax nodes the same node of the source: same kind and same range? (A node and the sequence that
holds only it share a range, so the kind is needed.) -/
private def sameNode (a b : Syntax) : Bool :=
  a.getKind == b.getKind && a.getPos?.isSome && a.getPos? == b.getPos? && a.getTailPos? == b.getTailPos?

/-- Replace the node with the same source range as `target` by `replacement`; `none` when it is not there. -/
partial def replaceNode (stx target replacement : Syntax) : Option Syntax :=
  if sameNode stx target then some replacement else
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
def closeAndEmit (proof : TSyntax `tactic) (leavesGoals : Bool := false) : TacticM Unit := do
  let s₀ ← saveState
  let goal ← getMainGoal
  let errors := fun (log : MessageLog) =>
    log.reportedPlusUnreported.toList.filter (·.severity == .error)
  let before := (errors (← Core.getMessageLog)).length
  -- a non-backtracking catch: the handler must read the errors the failed run logged before restoring them away
  Tactic.tryCatch
    (do
      -- no error recovery: a checker failing inside a nested `by` must fail the tactic, not be logged
      -- postponed elaboration problems (a `by` block whose type still has metavariables) are solved here, so their
      -- failures count against this proof instead of surfacing after it was accepted
      let others := (← getGoals).filter (· != goal)
      Term.withoutErrToSorry <| withoutRecover <| do
        evalTactic proof
        Term.synthesizeSyntheticMVarsNoPostponing
      -- a block that leaves goals open is not a proof, unless it declared them for the next tactic (a rewrite
      -- step): refuse it before anything is reported
      let unsolved := (← getUnsolvedGoals).filter (!others.contains ·)
      unless unsolved.isEmpty || leavesGoals do
        throwError "unsolved goals\n{goalsToMessageData unsolved}"
      let logged := (errors (← Core.getMessageLog)).drop before
      unless logged.isEmpty do
        let texts ← logged.mapM fun m => m.data.toString
        throwError "veriphy: the certificate check failed:\n{"\n".intercalate texts}"
      checkAxioms goal)
    fun ex => do
      let texts ← ((errors (← Core.getMessageLog)).drop before).mapM fun m => m.data.toString
      s₀.restore
      -- the restore drops the logged errors, and an error mentioning a sorry they left is not shown at all: carry
      -- both in one error
      match ex with
      | .error _ msg =>
        let main ← msg.toString
        -- already combined above, from the errors the proof logged
        if texts.isEmpty || main.startsWith "veriphy: the certificate check failed:" then throw ex
        let all := (texts.filter (· != main)) ++ [main]
        throwError "veriphy: the certificate check failed:\n{"\n".intercalate all}"
      | .internal id _ =>
        if !isAbortExceptionId id then throw ex
        let reason := if texts.isEmpty then ["the proof was aborted"] else texts
        throwError "veriphy: the certificate check failed:\n{"\n".intercalate reason}"
  -- emit what ran: a `first | …` becomes the alternative that closed its goal (the replay checks the result)
  let proof : TSyntax `tactic := ⟨← keepRunAlternatives s₀ proof⟩
  if veriphy.checkReplay.get (← getOptions) then
    replay s₀ proof (← getUnsolvedGoals)
  Lean.Meta.Tactic.TryThis.addSuggestion (← getRef) proof (header := "Sage-free replacement: ")


end Veriphy
