# name: operator_identity
# technique: operator identities: matrix commutators entrywise, differential operators on a test function
# goal: a commutator or composition of explicit matrices, or of differential operators applied to a function ψ
# description: Sage computes the commutators; Lean proves matrix ones entrywise and differential ones by derivative lemmas.
MATRICES = None  # EDIT: matrices over ℚ(i) (Sage), for the commutators [Xᵢ, Xⱼ] of named Lean matrices
NAMES = None  # EDIT: their Lean names (definitions over ℂ), in the same order
PAIRS = None  # EDIT: the pairs (i, j) the goal states, or None for every i < j
COORDINATES = None  # EDIT: Coordinates(n) for differential operators in n variables
LHS = None  # EDIT: the left operator, from COORDINATES.partial(i), COORDINATES.multiplication(e), commutator(a, b)
RHS = None  # EDIT: the right operator
CLOSE = 'trivial'  # EDIT: the tactic closing the goal from the facts, e.g. 'simpa using hop'
if MATRICES is not None:
    facts = operator_relations(MATRICES, NAMES, PAIRS)
elif LHS is not None:
    facts = operator_identity(LHS, RHS, COORDINATES)
else:
    raise AssertionError('fill in MATRICES and NAMES, or COORDINATES, LHS and RHS, in a copy')
proof = steps(facts, tactic(CLOSE))
