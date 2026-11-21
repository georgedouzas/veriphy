/-
The `#veriphy` command's verbs that need no Sage: `level`, `export`, `translate`, `translations`, `coverage` and
`help`. Each expands to the elaborator of its deprecated name; `Veriphy.Tactic.Operation` adds the verbs that run
Sage, and the `veriphy` tactic.
-/
import Veriphy.Kit.Levels
import Veriphy.Kit.Graph
import Veriphy.Kit.Inspect
import Veriphy.Kit.Packs
import Veriphy.Kit.Coverage

namespace Veriphy

open Lean Elab Command

/-- `#veriphy level p₁ …`: each theorem under the prefixes, with its level. -/
syntax (name := veriphyLevelCommand) "#veriphy " &"level" (ppSpace ident)+ : command

/-- `#veriphy export p₁ … ["file.nt"]`: the formalized claims under the prefixes, for the claim graph. -/
syntax (name := veriphyExportCommand) "#veriphy " &"export" (ppSpace ident)+ (ppSpace str)? : command

/-- `#veriphy translate t`: how the term `t` reaches Sage, its atoms and its conditions. -/
syntax (name := veriphyTranslateCommand) "#veriphy " &"translate " term : command

/-- `#veriphy translations`: the translation tables in force here. -/
syntax (name := veriphyTranslationsCommand) "#veriphy " &"translations" : command

/-- `#veriphy coverage [p, …] ["file.json"]`: how much of a corpus's goals the translation reaches. -/
syntax (name := veriphyCoverageCommand) "#veriphy " &"coverage " "[" ident,* "]" (str)? : command

/-- `#veriphy help`: the verbs of the `veriphy` tactic and the `#veriphy` command. -/
syntax (name := veriphyHelpCommand) "#veriphy " &"help" : command

macro_rules
  | `(#veriphy level $ps*) => `(#veriphy_levels $ps*)
  | `(#veriphy export $ps* $[$out]?) => `(#veriphy_graph $ps* $[$out]?)
  | `(#veriphy translate $t) => `(#veriphy_translate $t)
  | `(#veriphy translations) => `(#veriphy_tables)
  | `(#veriphy coverage [$ps,*] $[$out]?) => `(#veriphy_coverage [$ps,*] $[$out]?)

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
