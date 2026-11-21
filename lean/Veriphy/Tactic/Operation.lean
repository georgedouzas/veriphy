/-
One tactic and one command run Veriphy's operations in Lean:

- `veriphy <verb> …` acts on the current goal: `veriphy certify "<script>"` closes it with the proof a script finds,
  and `veriphy search "<script>"` runs a script for guidance, closing nothing;
- `#veriphy <verb> …` acts on a named claim or the project: here `meaning`, `test` and `translations check`, and in
  `Veriphy.Kit.Operation` the verbs that need no Sage: `level`, `export`, `translate`, `translations`, `coverage`
  and `help`, which lists them all.

A script is given inline, or by the name of a saved `.sage` file in `.veriphy/certificates/`.
-/
import Veriphy.Tactic.SageRun
import Veriphy.Tactic.SageTest
import Veriphy.Tactic.Meaning
import Veriphy.Tactic.CheckTranslations
import Veriphy.Kit.Operation

namespace Veriphy

open Lean Elab Tactic Command

/-- Whether a script argument names a saved script file rather than holding the script itself. -/
def isScriptFile (s : String) : Bool :=
  s.endsWith ".sage" && !s.any (fun c => c == '\n' || c == ' ')

/-- `veriphy certify "<script>"` (or `"<name>.sage"`): close the goal with the proof the script finds; the kernel
checks it, and the proof is emitted as a Sage-free replacement. -/
syntax (name := veriphyCertify) "veriphy " &"certify " str : tactic

/-- `veriphy search "<script>"` (or `"<name>.sage"`): run a proof script and show what it finds, closing nothing. -/
syntax (name := veriphySearch) "veriphy " &"search " str : tactic

/-- The script an argument gives: the argument itself, or the saved `.sage` file it names. -/
def scriptOf (s : String) : IO String :=
  if isScriptFile s then readScript s else pure s

elab_rules : tactic
  | `(tactic| veriphy certify $s:str) => do sageRunCore (← scriptOf s.getString)

elab_rules : tactic
  | `(tactic| veriphy search $s:str) => do
    let script ← scriptOf s.getString
    let (lean, stdout, _) ← withLenientProblem fun p => do
      let problem ← p.toJson
      Kit.run "run" (Bridge.run problem script)
    let out := if stdout.all Char.isWhitespace then "" else s!"\n── script output ──\n{stdout.trimAsciiEnd}"
    logInfo m!"veriphy search: the script found\n{lean}{out}"

/-- `#veriphy meaning c [seed s] [values n] [points "<json>"]`: test whether the statement of `c` says what it was
meant to, at seeded values satisfying its hypotheses. -/
syntax (name := veriphyMeaningCommand) "#veriphy " &"meaning " ident (ppSpace &"seed " num)?
  (ppSpace &"values " num)? (ppSpace &"points " str)? : command

/-- `#veriphy test c "<script>"` (or `"<name>.sage"`): check the claim `c` at the instances the script chooses. -/
syntax (name := veriphyTestCommand) "#veriphy " &"test " ident ppSpace str : command

/-- `#veriphy translations check ["<dir>"]`: check every project translation entry. -/
syntax (name := veriphyCheckCommand) "#veriphy " &"translations " &"check" (ppSpace str)? : command

elab_rules : command
  | `(#veriphy meaning $c:ident $[seed $s]? $[values $n]? $[points $p]?) =>
    meaningCore c (s.map (·.getNat) |>.getD 0) (n.map (·.getNat) |>.getD meaningDefaultValues)
      (p.map (·.getString))
  | `(#veriphy test $c:ident $s:str) => do sageTestCore (← getRef) c (← scriptOf s.getString)
  | `(#veriphy translations check $[$dir]?) => checkTranslationsCore (dir.map (·.getString) |>.getD "")

end Veriphy
