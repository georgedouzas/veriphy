/-
The old names of Veriphy's tactic and commands (`sage_run`, `sage_test`, `#veriphy_meaning`, …) keep working for one
minor release. Each warns when a user writes it, and stays silent when the new form (`veriphy certify`,
`#veriphy meaning`, …) expands to it, since a macro's output carries synthetic source positions.
-/
import Lean

namespace Veriphy

open Lean

/-- Warn that `old`, written at `stx`, is deprecated in favour of `new`, unless a macro wrote it. -/
def warnDeprecated {m : Type → Type} [Monad m] [MonadLog m] [AddMessageContext m] [MonadOptions m]
    (stx : Syntax) (old new : String) : m Unit := do
  if stx.getHeadInfo matches .original .. then
    logWarningAt stx m!"`{old}` is deprecated: use `{new}`; the old form goes in the next minor release"

end Veriphy
