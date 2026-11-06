/-
`sage_test`: check a claim no recipe can certify, by testing it at instances.

`sage_test c file "<name>.sage"` (or `sage_test c "<script>"`) opens the universal binders of the claim `c` (a theorem,
or a definition of type `Prop`), serializes them and the body as a problem, and runs the script, which assigns
`instances`. A kernel instance gives a value for every binder and a tactic block; Lean states the claim at the values
with `veriphy_instance%` (from the statement, never the proof), runs the block, and accepts it when it closes the goal
with the standard axioms and its proof does not depend on `c`, directly or through declarations of this module. An
oracle instance carries Sage's exact or interval evaluation, which Lean records but cannot check.

A run needs three accepted instances, one of them an edge case. Its Sage-free replacement is the accepted kernel
instances as `example`s and the attribute `veriphy_tested` with the level and the counts; every run also writes the
test record `.veriphy/tests/<c>.json`.
-/
import Veriphy.Kit
import Veriphy.Kit.Levels

namespace Veriphy

open Lean Elab Meta Term Tactic Command

/-- The fewest accepted instances a test needs. -/
def minInstances : Nat := 3

/-- Check one kernel instance: the claim at the values, proved by the block, independently of the claim. Returns
`none` when accepted, or the reason. -/
def checkInstance (target : Name) (values : Array String) (proof : String) : TermElabM (Option String) := do
  let statementText := s!"veriphy_instance% {target}" ++ String.join (values.toList.map (s!" ({·})"))
  let .ok statementStx := Parser.runParserCategory (← getEnv) `term statementText
    | return some s!"the values do not parse: {statementText}"
  let .ok proofStx := Parser.runParserCategory (← getEnv) `tactic ("(" ++ "\n ".intercalate (proof.splitOn "\n") ++ ")")
    | return some "the proof block does not parse"
  let saved ← saveState
  let before := (← Core.getMessageLog).reportedPlusUnreported.toList.length
  try
    let ty ← withoutErrToSorry do
      let ty ← elabType statementStx
      synthesizeSyntheticMVarsNoPostponing
      instantiateMVars ty
    let goal ← mkFreshExprMVar ty
    let remaining ← withoutErrToSorry <| Tactic.run goal.mvarId! do
      evalTactic proofStx
      Term.synthesizeSyntheticMVarsNoPostponing
    let errors := ((← Core.getMessageLog).reportedPlusUnreported.toList.drop before).filter (·.severity == .error)
    let result ← if !remaining.isEmpty then pure (some "the block does not close the instance")
      else if !errors.isEmpty then
        pure (some s!"the block fails: {← errors.head!.data.toString}")
      else
        try
          checkAxioms goal.mvarId!
          match ← dependence target (← instantiateMVars goal) with
          | some chain => pure (some s!"the proof depends on `{target}` (through {chain}), so it tests nothing")
          | none => pure none
        catch ex => pure (some (← ex.toMessageData.toString))
    saved.restore
    return result
  catch ex =>
    let reason ← ex.toMessageData.toString
    saved.restore
    return some reason

/-- One instance as Lean reads it from the daemon, with its outcome. -/
structure Outcome where
  values : Array String
  kind : String
  edge : Bool
  proof : String := ""
  evaluation : String := ""
  /-- `none` when accepted, otherwise why not. -/
  rejected : Option String := none

/-- Write the test record `.veriphy/tests/<target>.json`. -/
def writeRecord (target : Name) (statement level script : String) (problem : Json) (seed : Nat)
    (sageVersion : String) (outcomes : Array Outcome) : IO Unit := do
  let dir := (← projectDir) / "tests"
  IO.FS.createDirAll dir
  let instances := outcomes.map fun o => Json.mkObj [("values", Json.arr (o.values.map Json.str)),
    ("kind", Json.str o.kind), ("edge", Json.bool o.edge), ("accepted", Json.bool o.rejected.isNone),
    ("reason", Json.str (o.rejected.getD "")), ("evaluation", Json.str o.evaluation)]
  let record := Json.mkObj [("target", Json.str target.toString), ("statement", Json.str statement),
    ("level", Json.str level), ("seed", Json.num seed), ("sage_version", Json.str sageVersion),
    ("script_hash", Json.str s!"{hash script}"), ("script", Json.str script), ("problem", problem),
    ("instances", Json.arr instances)]
  IO.FS.writeFile (dir / s!"{target}.json") (record.pretty ++ "\n")

/-- The replacement: the accepted kernel instances as examples, and the level attribute. -/
def testReplacement (target : Name) (level : String) (outcomes : Array Outcome) : String :=
  let accepted := outcomes.filter (·.rejected.isNone)
  let kernel := accepted.filter (·.kind == "kernel")
  let examples := kernel.map fun o =>
    let values := String.join (o.values.toList.map (s!" ({·})"))
    s!"example : veriphy_instance% {target}{values} := by\n  " ++ "\n  ".intercalate (o.proof.splitOn "\n")
  let attr := s!"attribute [veriphy_tested {level.replace "-" "_"} {kernel.size} {accepted.size - kernel.size}] {target}"
  "\n\n".intercalate (examples.toList ++ [attr])

/-- Run a test script against the claim `target`. -/
def sageTestRun (ref : Syntax) (target : Ident) (script : String) : TermElabM (Name × String) := do
  let name ← realizeGlobalConstNoOverloadWithInfo target
  let (problem, binders) ← claimProblem name
  let (instances, stdout, seed, sageVersion) ← Kit.run "test" (Bridge.test problem script)
  let mut outcomes : Array Outcome := #[]
  for j in instances do
    let values := ((j.getObjValAs? (Array String) "values").toOption.getD #[])
    let kind := (j.getObjValAs? String "kind").toOption.getD "kernel"
    let edge := (j.getObjValAs? Bool "edge").toOption.getD false
    if values.size != binders then
      outcomes := outcomes.push { values, kind, edge, rejected := some s!"{values.size} values for {binders} binders" }
    else if kind == "oracle" then
      let evaluation := (j.getObjValAs? String "evaluation").toOption.getD ""
      unless (j.getObjValAs? Bool "verdict").toOption.getD false do
        throwError "sage_test: Sage refutes `{name}` at {values}: {evaluation}"
      outcomes := outcomes.push { values, kind, edge, evaluation }
    else
      let proof := (j.getObjValAs? String "proof").toOption.getD ""
      outcomes := outcomes.push { values, kind, edge, proof, rejected := ← checkInstance name values proof }
  let accepted := outcomes.filter (·.rejected.isNone)
  let rejectedLines := (outcomes.filter (·.rejected.isSome)).toList.map fun o =>
    s!"  at {o.values}: {o.rejected.getD ""}"
  let level := if accepted.any (·.kind == "oracle") then "oracle-test" else "kernel-test"
  let statement := toString (← ppExpr (← instantiateMVars (← claimStatement name)))
  writeRecord name statement level script problem seed sageVersion outcomes
  if accepted.size < minInstances || !accepted.any (·.edge) then
    let need := s!"a test needs {minInstances} accepted instances, one of them an edge case; it has {accepted.size}" ++
      (if accepted.any (·.edge) then "" else " and no edge case")
    let details := if rejectedLines.isEmpty then "" else "\nrejected:\n" ++ "\n".intercalate rejectedLines
    let out := if stdout.all Char.isWhitespace then "" else s!"\n── script output ──\n{stdout}"
    throwError "sage_test: {need}{details}{out}"
  for line in rejectedLines do
    logWarning s!"sage_test: an instance is rejected:\n{line}"
  let replacement := testReplacement name level outcomes
  Lean.Meta.Tactic.TryThis.addSuggestion ref (.string replacement : Lean.Meta.Tactic.TryThis.SuggestionText)
    (header := "Sage-free replacement: ")
  return (name, replacement.splitOn "\n" |>.getLast!)

/-- Run a test script against the claim `target`, and give the claim its level now, by the replacement's own
attribute command. -/
def sageTestCore (ref : Syntax) (target : Ident) (script : String) : CommandElabM Unit := do
  let (_, attr) ← liftTermElabM (sageTestRun ref target script)
  match Parser.runParserCategory (← getEnv) `command attr with
  | .ok stx => elabCommand stx
  | .error e => throwError "sage_test: the level attribute does not parse ({e}): {attr}"

/-- `sage_test c "<script>"`: test the claim `c` at the instances the script chooses. -/
syntax (name := sageTest) "sage_test " ident ppSpace str : command

/-- `sage_test c file "<name>.sage"`: test the claim `c` with a saved script from `.veriphy/certificates/`. -/
syntax (name := sageTestFile) "sage_test " ident ppSpace &"file " str : command

elab_rules : command
  | `(sage_test $c:ident $s:str) => do sageTestCore (← getRef) c s.getString
  | `(sage_test $c:ident file $p:str) => do sageTestCore (← getRef) c (← readScript p.getString)

end Veriphy
