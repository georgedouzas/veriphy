/-
The kit `veriphy certify` is built from.

  Kit.Problem  goal + context → normalized problem (lenient: text for anything without a polynomial form)
  Kit.Family   `closeAndEmit`: run what you print, reject `sorry` and non-standard axioms, emit once
  Kit.Replay   `veriphy.checkReplay` and the guarded Sage session entry point `Kit.run`/`Kit.call`
  Kit.Project  the project's `.veriphy/` directory and script path resolution
  Kit.Packs    the library packs Veriphy ships and `#veriphy translations`
  Kit.Coverage `#veriphy coverage`: how much of a corpus the symbolic translation covers
  Kit.Inspect  `#veriphy translate`: the symbolic translation of a term, without Sage
  Kit.Levels   verification levels: `veriphy_certified`, `veriphy_tested`, `veriphy_instance%`, `#veriphy level`
  Kit.Claim    a claim's universal binders and body as a problem, and dependence on a claim
  Kit.Linear   packaging lemmas for linear-algebra certificates (minors, factorisations, kernels, signatures)
  Kit.Graph    `#veriphy export`: the formalized claims, levels and dependencies for the research claim graph
-/
import Veriphy.Kit.Problem
import Veriphy.Kit.Packs
import Veriphy.Kit.Family
import Veriphy.Kit.Replay
import Veriphy.Kit.Project
import Veriphy.Kit.Coverage
import Veriphy.Kit.Inspect
import Veriphy.Kit.Linear
import Veriphy.Kit.Levels
import Veriphy.Kit.Claim
import Veriphy.Kit.Graph
import Veriphy.Kit.Operation
