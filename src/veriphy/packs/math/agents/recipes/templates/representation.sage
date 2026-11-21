# name: representation
# technique: explicit representations and their decompositions, every claim an identity of explicit matrices
# goal: matrices form a representation; a decomposition, branching or Clebsch-Gordan statement about them
# description: Sage builds the matrices and finds projectors, intertwiners or a change of basis; the kernel checks each.
REPRESENTATION = None  # EDIT: the matrices (Sage), e.g. tensor_representation(rho, sigma)
TABLE = None  # EDIT: the algebra's structure constants on the same basis, to prove the bracket relations
CASIMIR = None  # EDIT: a matrix whose eigenspaces are the summands (a Casimir), for projectors onto them
SUMMANDS = None  # EDIT: bases (as columns) of invariant subspaces, for a change of basis to block form
TARGET = None  # EDIT: a second representation on the same basis, for an intertwiner from REPRESENTATION to it
CLOSE = 'trivial'  # EDIT: the tactic closing the goal from the facts, e.g. 'exact ⟨hp_0, hp_1, hsum⟩'

assert REPRESENTATION is not None, 'fill in REPRESENTATION (and TABLE, CASIMIR, SUMMANDS or TARGET) in a copy'
facts = []
if TABLE is not None:
    facts.append(representation_relations(REPRESENTATION, TABLE))
if CASIMIR is not None:
    facts.append(projector_facts([p for _, p in eigen_projectors(CASIMIR)], REPRESENTATION))
if SUMMANDS is not None:
    change, blocks = decomposition(REPRESENTATION, SUMMANDS)
    facts.append(change_of_basis_facts(change, REPRESENTATION, blocks))
if TARGET is not None:
    found = intertwiners(REPRESENTATION, TARGET)
    assert found, 'no intertwiner: the representations share no irreducible summand'
    facts.append(intertwining_facts(found[0], REPRESENTATION, TARGET))
assert facts, 'fill in TABLE, CASIMIR, SUMMANDS or TARGET: there is nothing to prove'
proof = steps(*facts, tactic(CLOSE))
