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

namespace QuantumMechanics.HarmonicOscillator
open Complex Constants SchwartzMap

attribute [local instance 100] LieRing.ofAssociativeRing

variable {d : ℕ} (Q : HarmonicOscillator d) (i : Fin d)

-- [aᵢ, xᵢ] = ξᵢ/√2, with the ladder template unedited
example : ⁅Q.loweringCLM i, 𝐱 i⁆ = (((Q.ξ i : ℝ) : ℂ) / (Real.sqrt 2 : ℂ)) • ContinuousLinearMap.id ℂ 𝓢(Space d, ℂ) := by
  sage_run file "../prompts/recipes/physlib/templates/ladder_operators.sage"

-- [aᵢ + aᵢ†, pᵢ] = 2iℏ/(√2 ξᵢ), the scalar computed by Sage first
example : ⁅Q.loweringCLM i + Q.raisingCLM i, 𝐩 i⁆ =
    (2 * I * (ℏ : ℂ) / ((Real.sqrt 2 : ℂ) * ((Q.ξ i : ℝ) : ℂ))) • ContinuousLinearMap.id ℂ 𝓢(Space d, ℂ) := by
  sage_run "
xi, hbar = var('xi hbar')
c = canonical_commutator(ladder_combination({'a': 1, 'a†': 1}), ladder_combination({'p': 1}))
assert bool(c == 2 * I * hbar / (sqrt(2) * xi)), c
proof = ladder_commutator_proof()"

end QuantumMechanics.HarmonicOscillator
