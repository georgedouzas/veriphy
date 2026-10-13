/-
`#veriphy_check_translations` checks every entry of the project's translation tables against Sage and Lean:

* a function entry's `example` is translated to Sage, rendered back by the toolkit, and the rendering is proved
  equal to the original by `linear_combination` (through `sage_run`, so Sage must be installed);
* a rewrite entry's `example`, a signature `(x : ℝ) (hx : x ≠ 0) : goal`, is closed by rewriting with its lemma.

Each entry is reported as passed or failed, with Lean's error.
-/
import Veriphy.Tactic.SageRun

namespace Veriphy

open Lean Elab Command

/-- The round-trip script: render the hypothesis back and prove it equal to the original. -/
def roundTripScript : String :=
  "h = hyps[0]\n" ++
    "assert h.expr is not None, 'Sage could not read the translation: check the sage name'\n" ++
    "proof = steps(tactic(f'have _r : {symbolic(h.expr, problem)} = 0 := by linear_combination {h.name}'), " ++
    "tactic('trivial'))"

/-- The one-letter variables of an example term, in order of appearance (not part of a dotted name). -/
def exampleVariables (example_ : String) : List String := Id.run do
  let chars := example_.toList.toArray
  let mut vars : List String := []
  for h : i in [0:chars.size] do
    let c := chars[i]
    let before := if i == 0 then ' ' else chars[i - 1]!
    let after := chars[i + 1]?.getD ' '
    if c.isAlpha && !before.isAlphanum && before != '.' && !after.isAlphanum && after != '.' && after != '_' then
      if !vars.contains c.toString then vars := vars ++ [c.toString]
  return vars

/-- The Lean source checking one function entry. -/
def functionCheck (dir : String) (f : FunctionEntry) : String :=
  let ty := f.types.headD "ℝ"
  let binders := " ".intercalate ((exampleVariables f.«example»).map (s!"({·} : {ty})"))
  let lhs := if ["ℕ", "ℤ"].contains f.result then s!"((({f.«example»}) : {f.result}) : ℝ)" else s!"({f.«example»})"
  s!"set_option veriphy.translationsDir \"{dir}\" in\nexample {binders} (h : {lhs} = 0) : True := by\n" ++
    s!"  sage_run \"{roundTripScript}\""

/-- The Lean source checking one rewrite entry. -/
def rewriteCheck (r : RewriteEntry) : String :=
  let rule := (if r.reverse then "← " else "") ++ r.«lemma»
  s!"example {r.«example»} := by\n  rw [{rule}]\n  all_goals first | rfl | assumption | positivity | ring_nf"

/-- Elaborate a generated check, returning Lean's errors (empty when it passed); its messages are not kept. -/
def runCheck (source : String) : CommandElabM (List String) := do
  let saved := (← get).messages
  modify fun st => { st with messages := {} }
  let errors ← try
      match Parser.runParserCategory (← getEnv) `command source "<veriphy check>" with
      | .error e => pure [s!"does not parse: {e}"]
      | .ok stx =>
        withoutModifyingEnv (elabCommand stx)
        let msgs := (← get).messages.toList.filter (·.severity == .error)
        msgs.mapM (·.data.toString)
    catch ex => pure [← ex.toMessageData.toString]
  modify fun st => { st with messages := saved }
  return errors

/-- `#veriphy_check_translations` (or with a directory) — check every project entry; see the module doc. -/
syntax (name := veriphyCheckTranslations) "#veriphy_check_translations" (str)? : command

elab_rules : command
  | `(#veriphy_check_translations $[$dir]?) => do
    let dir := match dir with | some d => d.getString | none => ""
    let (tables, problems) ← liftIO (projectTables dir)
    for p in problems do logError m!"invalid: {p}"
    let mut report := #[]
    let mut failed := 0
    for t in tables do
      for f in t.functions do
        let errors ← runCheck (functionCheck dir f)
        if errors.isEmpty then report := report.push s!"passed: {f.lean} ↔ {f.sage}"
        else
          failed := failed + 1
          report := report.push s!"failed: {f.lean} ↔ {f.sage}: {errors.headD ""}"
      for r in t.rewrites do
        let errors ← runCheck (rewriteCheck r)
        if errors.isEmpty then report := report.push s!"passed: rw [{r.«lemma»}]"
        else
          failed := failed + 1
          report := report.push s!"failed: rw [{r.«lemma»}]: {errors.headD ""}"
    let text := "\n".intercalate report.toList
    if failed == 0 then logInfo text else logError text

end Veriphy
