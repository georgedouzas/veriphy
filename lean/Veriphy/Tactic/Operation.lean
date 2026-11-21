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

macro_rules
  | `(tactic| veriphy certify $s:str) =>
    if isScriptFile s.getString then `(tactic| sage_run file $s) else `(tactic| sage_run $s)

elab_rules : tactic
  | `(tactic| veriphy search $s:str) => do
    let script ← if isScriptFile s.getString then readScript s.getString else pure s.getString
    let (lean, stdout, _, _) ← withLenientProblem fun p => do
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

macro_rules
  | `(#veriphy meaning $c:ident $[seed $s]? $[values $n]? $[points $p]?) =>
    `(#veriphy_meaning $c:ident $[seed $s]? $[values $n]? $[points $p]?)
  | `(#veriphy test $c:ident $s:str) =>
    if isScriptFile s.getString then `(sage_test $c:ident file $s) else `(sage_test $c:ident $s)
  | `(#veriphy translations check $[$dir]?) => `(#veriphy_check_translations $[$dir]?)

end Veriphy
