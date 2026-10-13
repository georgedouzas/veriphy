# Lie superalgebras

## When to use

- The goal is about a **ℤ/2-graded** Lie algebra given concretely:
  - graded brackets of explicit supermatrices (`sl(1|1)`, `osp(1|2)`, `gl(m|n)` elements): anticommutators of odd
    elements, commutators otherwise;
  - the super-Jacobi identity of a superalgebra given by structure constants, including the exceptional
    `D(2,1;α)` (for every α at once), `G(3)` and `F(4)`.
- Sage builds the brackets. For supermatrices, `parity_of(m, even_dim)`, `graded_commutator`, `supertrace`,
  `supertrace_form` and `super_casimir`. For the exceptional families, the construction `g₀ ⊕ V` with the odd
  bracket the moment map of an invariant symplectic form on `V`: `contragredient_superalgebra(even_ops, factors,
  omega)` solves the super-Jacobi condition on three odd vectors (linear in the moment-map coefficients), and
  `d21_alpha`, `g3`, `f4` build `sl₂³` on `2⊗2⊗2`, `G₂ ⊕ sl₂` on `7⊗2` and `so(7) ⊕ sl₂` on `8⊗2`.
- Lean checks every claim: graded brackets entrywise by the kernel (`VeriphyCheck.eq_of_check`), and super-Jacobi on
  every basis triple by `VeriphyCheck.Sparse.superJacobi_of_check`, whose cost follows the nonzero products of
  structure constants. For `D(2,1;α)`, `VeriphyCheck.Sparse.superJacobi_affine` proves the identity for every α in a
  field of characteristic zero from the checks at α = 0, 1 and -1 (the sums are quadratic in α).

## Template

Copy it to the project's `.veriphy/certificates/lie_superalgebra.sage` (or a more specific name), adapt the lines
marked `EDIT`, keep the header, and run it with `sage_run file "<name>.sage"`.

```sage
# name: lie_superalgebra
# technique: Lie superalgebras of supermatrices or by structure constants; graded brackets and super-Jacobi checked by Lean
# goal: graded brackets of explicit supermatrices, or the super-Jacobi identity of sl(m|n), osp, D(2,1;α), G(3), F(4)
# description: Sage builds the brackets (the moment map for the exceptional families); the kernel checks each identity.
SUPERMATRICES = None  # EDIT: homogeneous supermatrices (Sage), for graded bracket relations between named matrices
EVEN_DIM = None  # EDIT: the dimension of the even part of the superspace they act on
NAMES = None  # EDIT: the Lean names of the supermatrices, in the same order
ALGEBRA = None  # EDIT: 'D21' (the family, for every α), 'G3' or 'F4', for the super-Jacobi identity of the algebra
CLOSE = 'trivial'  # EDIT: the tactic closing the goal from the facts, e.g. 'exact ⟨hs_3_4, hs_3_3⟩'

if SUPERMATRICES is not None:
    parities = [parity_of(m, EVEN_DIM) for m in SUPERMATRICES]
    facts = super_relations(SUPERMATRICES, parities, NAMES)
elif ALGEBRA == 'D21':
    t0, parities = d21_alpha(QQ(0))
    t1p, _ = d21_alpha(QQ(1))
    n = len(t0)
    t1 = [[[t1p[i][j][k] - t0[i][j][k] for k in range(n)] for j in range(n)] for i in range(n)]
    facts = super_jacobi_family_certificate(t0, t1, parities)
elif ALGEBRA in ('G3', 'F4'):
    table, parities = g3() if ALGEBRA == 'G3' else f4()
    table, scales = integral_rescaling(table, parities)
    facts = super_jacobi_certificate(table, parities)
else:
    raise AssertionError('fill in SUPERMATRICES (with EVEN_DIM and NAMES) or ALGEBRA in a copy')
proof = steps(facts, tactic(CLOSE))
```

## Worked examples

```lean
-- with ALGEBRA = 'D21': super-Jacobi for D(2,1;α) and every real α
set_option maxHeartbeats 0 in
example : True := by
  sage_run file "lie_superalgebra_d21.sage"

-- osp(1|2) on (1|2), with SUPERMATRICES, EVEN_DIM = 1 and NAMES filled in
example : qp * qm + qm * qp = -h ∧ qp * qp + qp * qp = 2 • e := by
  sage_run file "osp12.sage"
-- replacement: have hs_i_j : … := VeriphyCheck.eq_of_check (by decide +kernel) for each pair, then the CLOSE tactic
```

`VeriphyTest/SageRun.lean` runs these, and `G(3)` (31-dimensional).

## Failure modes

- **"fill in SUPERMATRICES … or ALGEBRA":** copy the template and choose what to prove.
- **"the supermatrix is not homogeneous":** an element mixes even and odd blocks; split it.
- **"has the wrong parity":** the parities given do not match the brackets (an even element labelled odd).
- **"N independent moment-map coefficients satisfy super-Jacobi; pass them":** the construction admits a family
  (as `D(2,1;α)` does); pass the coefficients of the member you want.
- **"super-Jacobi fails at (i, j, k, m)":** the table is not a Lie superalgebra; the message names a basis triple and
  coordinate.
- **Slow kernel checks:** the sparse check costs about the number of nonzero products; raise `maxHeartbeats` (0
  disables the limit). Integral constants (`integral_rescaling`) check faster than rational ones.
- **Abstract superalgebras** (no supermatrices or structure constants in the goal): out of scope; mathlib has no
  Lie superalgebra structure yet, so state the claim on structure constants (`VeriphyCheck.superJacobiAt`) and
  report `blocked-library-gap` for the abstract statement.
