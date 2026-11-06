/-
Measure Veriphy's translation coverage on Physlib, mathlib's Archive, and mathlib's ODE, Lie-algebra and manifold
directories. Each `#veriphy_coverage` writes its report to `.veriphy/coverage/<prefix>.json` in this project.
-/
import Mathlib
import Archive
import Physlib
import Veriphy

#veriphy_coverage [Physlib]
#veriphy_coverage [Archive]
#veriphy_coverage [Mathlib.Analysis.ODE]
#veriphy_coverage [Mathlib.Algebra.Lie]
#veriphy_coverage [Mathlib.Geometry.Manifold]
