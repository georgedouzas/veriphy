# name: independence
# technique: linear independence from a non-singular minor, dependence from a relation, spans from coordinates
# goal: LinearIndependent K v, ¬ LinearIndependent K v, or span K (range v) = span K (range w) or = ker A.mulVecLin
# description: Sage finds the minor, the relation or the coordinates; Lean checks them by evaluation.
VECTORS = None  # EDIT: the family v as the goal states it, as [[1, 2, 0], [0, 1, 1]]
OTHER = None  # EDIT: for span (range v) = span (range w), the family w
KERNEL = None  # EDIT: for span (range v) = ker A.mulVecLin, the matrix A, as [[1, 1, 1]]
FIELD = 'ℚ'  # EDIT: the scalars of the goal
assert VECTORS is not None, 'fill in VECTORS (and OTHER or KERNEL for a span equality) in a copy'
if OTHER is not None or KERNEL is not None:
    kernel = matrix(QQ, KERNEL) if KERNEL is not None else None
    proof = tactic(span_proof(VECTORS, other=OTHER, kernel_of=kernel, field=FIELD))
else:
    proof = tactic(independence_proof(VECTORS, negated=goal.text.lstrip().startswith('¬')))
