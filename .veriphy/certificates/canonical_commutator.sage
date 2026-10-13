# name: canonical_commutator
# technique: operator identities: matrix commutators entrywise, differential operators on a test function
# goal: a commutator or composition of explicit matrices, or of differential operators applied to a function ψ
# description: Sage computes the commutators; Lean proves matrix ones entrywise and differential ones by derivative lemmas.
MATRICES = None  # EDIT: matrices over ℚ(i) (Sage), for the commutators [Xᵢ, Xⱼ] of named Lean matrices
NAMES = None  # EDIT: their Lean names (definitions over ℂ), in the same order
PAIRS = None  # EDIT: the pairs (i, j) the goal states, or None for every i < j
COORDINATES = Coordinates(1)
LHS = commutator(COORDINATES.partial(0), COORDINATES.multiplication(COORDINATES.symbols[0]))
RHS = COORDINATES.scalar(1)
CLOSE = 'simpa using hop'
if MATRICES is not None:
    facts = operator_relations(MATRICES, NAMES, PAIRS)
elif LHS is not None:
    facts = operator_identity(LHS, RHS, COORDINATES)
else:
    raise AssertionError('fill in MATRICES and NAMES, or COORDINATES, LHS and RHS, in a copy')
proof = steps(facts, tactic(CLOSE))
