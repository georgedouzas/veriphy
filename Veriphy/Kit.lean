/-
The kit `sage_run` is built from.

  Kit.Problem  goal + context → normalized problem (lenient: text for anything without a polynomial form)
  Kit.Family   `closeAndEmit`: run what you print, reject `sorry` and non-standard axioms, emit once
  Kit.Replay   `veriphy.checkReplay` and the guarded daemon entry point `Kit.run`/`Kit.call`
-/
import Veriphy.Kit.Problem
import Veriphy.Kit.Family
import Veriphy.Kit.Replay
