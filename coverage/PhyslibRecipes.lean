/-
The Physlib recipes on their worked examples. Needs a local Sage with `veriphy` installed, as `VeriphyTest/SageRun`.
-/
import Physlib
import Veriphy

-- the boost generator along x lies in the Lorentz algebra
example : Matrix.fromBlocks !![(0 : ℝ)] !![1, 0, 0] !![1; 0; 0] (0 : Matrix (Fin 3) (Fin 3) ℝ) ∈ lorentzAlgebra := by
  sage_run file "../prompts/recipes/physlib/templates/lorentz_algebra.sage"

-- the rotation generator in the y-z plane
example : Matrix.fromBlocks (0 : Matrix (Fin 1) (Fin 1) ℝ) 0 0 !![0, 0, 0; 0, 0, -1; 0, 1, 0] ∈ lorentzAlgebra := by
  sage_run file "../prompts/recipes/physlib/templates/lorentz_algebra.sage"
