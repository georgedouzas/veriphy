# name: smith_example
# technique: Smith and Jordan normal forms with explicit transformation matrices and inverses
# goal: a statement about the Smith form, Jordan form or diagonalization of an explicit matrix
# description: Sage computes the form and the transformations; the kernel checks U A V = D or A P = P J and the inverses.
MATRIX = matrix(ZZ, [[2, 4, 4], [-6, 6, 12], [10, -4, -16]])
FORM = 'smith'
CLOSE = 'trivial'  # EDIT: the tactic closing the goal from the facts (hsmith, hU, hV or hjordan, hP)
assert MATRIX is not None, 'fill in MATRIX (and FORM) in a copy'
if FORM == 'smith':
    d, u, v, facts = smith_certificate(MATRIX)
    print('D =', d.diagonal())
else:
    j, p, facts = jordan_certificate(MATRIX)
    print('J =', j)
proof = steps(facts, tactic(CLOSE))
