/-
The certificate kit: what a `sage_*` tactic is built from.

  Kit.Problem  goal + context → normalized constraint problem (shared atom table)
  Kit.Build    certificate data → re-parseable Lean syntax
  Kit.Family   checker families + `closeAndEmit` (run what you print, emit once)
  Kit.Replay   `veriphy.checkReplay` and the guarded daemon entry point `Kit.run`/`Kit.call`

A new certificate tactic is: `withProblem` → `Kit.run (Bridge.…)` → builders → a family's
`Checker.*` → `closeAndEmit`. See docs/development/index.md, "Adding a certificate".
-/
import Veriphy.Kit.Problem
import Veriphy.Kit.Build
import Veriphy.Kit.Family
import Veriphy.Kit.Replay
