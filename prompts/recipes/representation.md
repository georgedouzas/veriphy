# Representations

## When to use

- The goal is about **explicit representation matrices** of a Lie algebra:
  - they form a representation (they satisfy the algebra's bracket relations);
  - a representation decomposes: projectors onto the summands, or a change of basis to block form;
  - a branching rule through an explicit embedding (the 10 of SU(5) under SU(3)×SU(2)×U(1));
  - Clebsch-Gordan coefficients: a change of basis that intertwines a tensor product with a direct sum.
- Sage builds the matrices: `defining_representation('A4')` (Chevalley generators `eᵢ`, `fᵢ`, `hᵢ`),
  `spin_representation(2j)`, `adjoint_matrices(structure_constants(basis))`, `tensor_representation`,
  `exterior_square`, and `cyclic_submodule(rho, v)` for the irreducible module a highest weight vector `v`
  generates. It finds `eigen_projectors(casimir)`, `intertwiners(rho, sigma)`, `decomposition(rho, summands)` and
  `clebsch_gordan(2j₁, 2j₂)`.
- Every claim reaches Lean as matrix identities the kernel checks: bracket relations, `P * P = P`, `P * Q = 0`,
  `P + Q = 1`, `P * ρ(x) = ρ(x) * P`, `T * ρ(x) = σ(x) * T`, `ρ(x) * P = P * B(x)`, `P * P⁻¹ = 1`. Dimension and
  character counts are never offered as proofs.
- Matrices are in the Chevalley normalization (basis `fᵏv / k!`), where they are rational. The orthonormal basis of
  physics differs by a diagonal rescaling with square roots, which leaves intertwining and projector identities
  unchanged; when the goal states orthonormal matrices, rescale with the number-field toolkit
  (`quadratic_context`, `field_matrix_identity`).

## Template

Copy it to the project's `.veriphy/certificates/representation.sage` (or a more specific name), adapt the lines
marked `EDIT`, keep the header, and run it with `sage_run file "<name>.sage"`.

```sage
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
```

## Worked examples

```lean
-- with REPRESENTATION = tensor_representation(spin_representation(1), spin_representation(1)) and
-- CASIMIR = e*f + f*e + h*h/2: projectors onto spin 1 and spin 0, idempotent, orthogonal, complete, commuting
example : True := by
  sage_run file "rep_two_spins.sage"

-- in a script: the Clebsch-Gordan matrix of 1 ⊗ ½ intertwines the product with spin 3/2 ⊕ spin 1/2
example : True := by
  sage_run "
t, spins = clebsch_gordan(2, 1)
product = tensor_representation(spin_representation(2), spin_representation(1))
blocks = [block_diagonal_matrix([spin_representation(s)[k] for s in spins]) for k in range(3)]
proof = steps(intertwining_facts(t, product, blocks), tactic('trivial'))"
```

`VeriphyTest/SageRun.lean` also runs the adjoint of 𝔰𝔩₃ (28 bracket relations of 8×8 matrices) and the branching of
the 10 of SU(5).

## Failure modes

- **"fill in REPRESENTATION …":** the template needs the matrices; copy it and fill them in.
- **"the matrices i and j do not satisfy the bracket relation":** the matrices are not a representation on that
  basis; check the order of the basis against the structure constants.
- **"not diagonalizable over ℚ":** the Casimir has irrational eigenvalues or a Jordan block; the summands are not
  separated by it. Use another invariant, or give SUMMANDS directly.
- **"not invariant":** a claimed summand is not a subrepresentation.
- **Large representations** (dimension in the hundreds): every identity is a kernel check of `n³` operations; split the
  claim into blocks, or check fewer generators (the Chevalley generators suffice for a representation).
- **A claim mathlib cannot state yet** (a character formula, a categorical decomposition statement):
  report `blocked-library-gap` with the definition the statement needs, and prove the matrix identities instead.
