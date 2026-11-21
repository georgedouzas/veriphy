# name: matrix_normal_form
# technique: Smith and Jordan normal forms with explicit transformation matrices and inverses
# goal: a statement about the Smith form, Jordan form or diagonalization of an explicit matrix
# description: Sage computes the form and the transformations; the kernel checks U A V = D or A P = P J and the inverses.
MATRIX = None  # EDIT: the matrix (Sage), integer for a Smith form, rational with rational eigenvalues for a Jordan form
FORM = 'jordan'  # EDIT: 'smith' or 'jordan' (a diagonalizable matrix gets a diagonal Jordan form)
CLOSE = 'trivial'  # EDIT: the tactic closing the goal from the facts (hsmith, hU, hV or hjordan, hP)
assert MATRIX is not None, 'fill in MATRIX (and FORM) in a copy'
if FORM == 'smith':
    d, u, v, facts = smith_certificate(MATRIX)
    print('D =', d.diagonal())
else:
    j, p, facts = jordan_certificate(MATRIX)
    print('J =', j)
proof = steps(facts, tactic(CLOSE))
