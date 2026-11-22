/-
The `physlib` library pack: data for Physlib's notations and definitions, active only when Physlib is imported.
Veriphy does not import Physlib; every constant is named as a string and checked when the pack activates.
-/
import Veriphy.Kit.Table

namespace Veriphy.Packs

/-- Physlib's derivatives, coordinates, membership criteria, operator unfoldings and sign conventions. -/
def physlib : Pack where
  library := "Physlib"
  sentinel := "Time.deriv"
  table := {
    «namespace» := "physlib"
    functions := [
      -- `∂ₜ f t`, Physlib's time derivative `fderiv ℝ f t 1`
      { lean := "Time.deriv", sage := "diff", arity := 2, role := some "derivative",
        «example» := "Time.deriv (fun t => t.val ^ 2) t" },
      -- `∂[μ] f x`, the partial derivative along the coordinate `μ`
      { lean := "Space.deriv", sage := "diff", arity := 3, role := some "partial",
        «example» := "Space.deriv 0 (fun x => x 0 * x 1) x" }]
    coercions := ["Time.val"]
    rewrites := [
      { «lemma» := "lorentzAlgebra.mem_iff", functions := ["lorentzAlgebra"],
        «example» := "!![0, 1, 0, 0; 1, 0, 0, 0; 0, 0, 0, 0; 0, 0, 0, 0] ∈ lorentzAlgebra" },
      { «lemma» := "QuantumMechanics.HarmonicOscillator.loweringCLM_eq", functions := ["loweringCLM"] },
      { «lemma» := "QuantumMechanics.HarmonicOscillator.raisingCLM_eq", functions := ["raisingCLM"] },
      { «lemma» := "QuantumMechanics.angularMomentumDimThreeCLM_zero_eq", functions := ["angularMomentumDimThreeCLM"] },
      { «lemma» := "QuantumMechanics.angularMomentumDimThreeCLM_one_eq", functions := ["angularMomentumDimThreeCLM"] },
      { «lemma» := "QuantumMechanics.angularMomentumDimThreeCLM_two_eq", functions := ["angularMomentumDimThreeCLM"] }]
    conventions := some [
      { key := "metric_signature", value := "+---" },
      { key := "metric", value := "minkowskiMatrix = indefiniteDiagonal (Fin 1) (Fin d) ℝ" },
      { key := "angular_momentum", value := "⁅𝐋₃ 0, 𝐋₃ 1⁆ = (I * ℏ) • 𝐋₃ 2" },
      { key := "time_derivative", value := "∂ₜ f t = fderiv ℝ f t 1" }] }

end Veriphy.Packs
