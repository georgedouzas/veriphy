/-
The `#veriphy` command's verbs that need no Sage: `level`, `export`, `translate`, `translations`, `coverage` and
`help`. Each verb's syntax sits beside its elaborator, in the module this one imports for it;
`Veriphy.Tactic.Operation` adds the verbs that run Sage, and the `veriphy` tactic.
-/
import Veriphy.Kit.Levels
import Veriphy.Kit.Graph
import Veriphy.Kit.Inspect
import Veriphy.Kit.Packs
import Veriphy.Kit.Coverage

namespace Veriphy

open Lean Elab Command

/-- `#veriphy help`: the verbs of the `veriphy` tactic and the `#veriphy` command. -/
syntax (name := veriphyHelpCommand) "#veriphy " &"help" : command

/-- The lines `#veriphy help` prints. -/
def helpLines : List String := [
  "veriphy certify \"<script>\"   close the goal with the proof a script finds (a tactic)",
  "veriphy search \"<script>\"    show what a proof script finds, closing nothing (a tactic)",
  "#veriphy meaning c            test the statement of c at seeded values",
  "#veriphy test c \"<script>\"    check c at instances, by the kernel or Sage",
  "#veriphy level p …            the level of each theorem under the prefixes",
  "#veriphy export p …           the formalized claims under the prefixes, for the claim graph",
  "#veriphy translate t          how a term reaches Sage",
  "#veriphy translations [check] the translation tables in force, or a check of the project's entries",
  "#veriphy coverage [p, …]      how much of a corpus's goals the translation reaches",
  "A script is inline, or the name of a saved `.sage` file in `.veriphy/certificates/`."]

elab_rules : command
  | `(#veriphy help) => logInfo ("\n".intercalate helpLines)

end Veriphy
