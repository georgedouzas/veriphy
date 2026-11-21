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
