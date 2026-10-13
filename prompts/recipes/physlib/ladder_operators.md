# Ladder operators (Physlib)

Applies to goals about Physlib's harmonic oscillator (`Physlib.QuantumMechanics.HarmonicOscillator`).

## When to use

- The goal is a commutator of combinations of Physlib's lowering and raising operators `Q.loweringCLM i`,
  `Q.raisingCLM i`, positions `𝐱 i` and momenta `𝐩 i` (one coordinate), equal to a scalar times the identity:
  `⁅A, B⁆ = c • ContinuousLinearMap.id ℂ 𝓢(Space d, ℂ)`. Physlib proves `[aᵢ, aⱼ†] = δᵢⱼ`; this recipe covers the
  rest, such as `[aᵢ, xᵢ] = ξᵢ/√2` or `[aᵢ + aᵢ†, pᵢ] = √2 iℏ/ξᵢ`.
- Physlib's convention is `aᵢ = (xᵢ/ξᵢ + i ξᵢ pᵢ/ℏ)/√2` and `aᵢ† = (xᵢ/ξᵢ - i ξᵢ pᵢ/ℏ)/√2`. With `LEFT` and `RIGHT`
  filled in, Sage computes `c` from `[x, p] = iℏ` (in the symbols `xi` and `hbar`), so the goal can be stated with
  the right scalar.
- Lean unfolds the ladder operators, expands the bracket by bilinearity with Physlib's commutation lemmas, and closes
  the scalar identity by `field_simp` and `ring` (`i² = -1`, `(√2)² = 2`, `ξᵢ ≠ 0`, `ℏ ≠ 0`).
- The goal's file must make the bracket of operators a Lie ring, as Physlib's own files do:
  `attribute [local instance 100] LieRing.ofAssociativeRing`.

## Template

Copy it to the project's `.veriphy/certificates/ladder_operators.sage`, adapt the lines marked `EDIT`, keep the
header, and run it with `sage_run file "<name>.sage"`.

```sage
# name: ladder_operators
# technique: commutators of Physlib's ladder operators, positions and momenta, by bilinearity and [x, p] = iℏ
# goal: ⁅A, B⁆ = c • ContinuousLinearMap.id ℂ 𝓢(Space d, ℂ), A and B combinations of Q.loweringCLM i, Q.raisingCLM i, 𝐱 i, 𝐩 i
# description: Sage computes the scalar c; Lean unfolds the ladder operators and applies Physlib's commutation lemmas.
LEFT = None  # EDIT: A as coefficients of 'a', 'a†', 'x', 'p', as {'a': 1, 'a†': 1}, to compute c before Lean
RIGHT = None  # EDIT: B likewise
INDEX = 'i'  # EDIT: the coordinate index of the goal
OSCILLATOR = 'Q'  # EDIT: the HarmonicOscillator of the goal
if LEFT is not None and RIGHT is not None:
    # the scalar in Physlib's symbols: xi for Q.ξ i, hbar for ℏ
    print('c =', canonical_commutator(ladder_combination(LEFT), ladder_combination(RIGHT)))
proof = ladder_commutator_proof(index=INDEX, oscillator=OSCILLATOR)
```

## Worked examples

```lean
namespace QuantumMechanics.HarmonicOscillator
open Complex Constants SchwartzMap

attribute [local instance 100] LieRing.ofAssociativeRing

variable {d : ℕ} (Q : HarmonicOscillator d) (i : Fin d)

-- [aᵢ, xᵢ] = ξᵢ/√2, with the template unedited
example : ⁅Q.loweringCLM i, 𝐱 i⁆ = (((Q.ξ i : ℝ) : ℂ) / (Real.sqrt 2 : ℂ)) • ContinuousLinearMap.id ℂ 𝓢(Space d, ℂ) := by
  sage_run file "ladder_operators.sage"

-- [aᵢ + aᵢ†, pᵢ], the scalar computed first (LEFT = {'a': 1, 'a†': 1}, RIGHT = {'p': 1} prints 2iℏ/(√2 ξ))
example : ⁅Q.loweringCLM i + Q.raisingCLM i, 𝐩 i⁆ =
    (2 * I * (ℏ : ℂ) / ((Real.sqrt 2 : ℂ) * ((Q.ξ i : ℝ) : ℂ))) • ContinuousLinearMap.id ℂ 𝓢(Space d, ℂ) := by
  sage_run file "ladder_operators.sage"
```

## Failure modes

- **`failed to synthesize LieRing`:** the bracket of operators needs
  `attribute [local instance 100] LieRing.ofAssociativeRing` in the goal's file.
- **The scalar identity stays open after `field_simp`:** the goal's `c` is wrong; fill in `LEFT` and `RIGHT` and
  compare with the printed value.
- **Different coordinates (`[aᵢ, xⱼ]` with `i ≠ j`):** the commutators vanish through `δ[i,j]`; state the goal for one
  index, or case on `i = j` first.
- **"unknown operators":** only `a`, `a†`, `x` and `p` combine; products (such as the number operator) are handled
  by Physlib's `number_commutation_lowering` and its relatives.
