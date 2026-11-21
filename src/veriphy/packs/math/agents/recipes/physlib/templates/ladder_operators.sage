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
