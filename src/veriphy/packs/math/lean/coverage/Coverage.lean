/-
Measure Veriphy's translation coverage on Physlib, mathlib's Archive, and mathlib's ODE, Lie-algebra and manifold
directories. Each `#veriphy coverage` writes its report to `.veriphy/coverage/<prefix>.json` in this project.
-/
import Mathlib
import Archive
import Physlib
import Veriphy

#veriphy coverage [Physlib]
#veriphy coverage [Archive]
#veriphy coverage [Mathlib.Analysis.ODE]
#veriphy coverage [Mathlib.Algebra.Lie]
#veriphy coverage [Mathlib.Geometry.Manifold]
