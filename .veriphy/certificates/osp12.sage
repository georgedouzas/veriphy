# name: osp12
# technique: Lie superalgebras of supermatrices or by structure constants; graded brackets and super-Jacobi checked by Lean
# goal: graded brackets of explicit supermatrices, or the super-Jacobi identity of sl(m|n), osp, D(2,1;α), G(3), F(4)
# description: Sage builds the brackets (the moment map for the exceptional families); the kernel checks each identity.
def unit(i, j):
    m = matrix(QQ, 3, 3); m[i, j] = 1; return m
SUPERMATRICES = [unit(1, 1) - unit(2, 2), unit(1, 2), unit(2, 1), unit(1, 0) + unit(0, 2), unit(2, 0) - unit(0, 1)]
EVEN_DIM = 1
NAMES = ['SuperTest.h', 'SuperTest.e', 'SuperTest.f', 'SuperTest.qp', 'SuperTest.qm']
ALGEBRA = None  # EDIT: 'D21' (the family, for every α), 'G3' or 'F4', for the super-Jacobi identity of the algebra
CLOSE = 'exact ⟨hs_3_4, hs_3_3⟩'

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
