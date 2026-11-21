# name: dimension
# technique: finrank of spans, intersections, kernels of functionals and product spaces
# goal: Module.finrank K V = n, V a span of explicit vectors, an intersection of two spans, a kernel, or a product space
# description: Sage computes ranks and bases; Lean uses independence from minors, the dimension formula, rank-nullity.
KIND = 'span'  # EDIT: 'span', 'intersection', 'kernel' (of a functional) or 'product' (Fin n → K, Matrix, ⊗, Dual)
VECTORS = None  # EDIT: for 'span', the family as the goal states it
FIRST, SECOND = None, None  # EDIT: for 'intersection', the two independent families
FUNCTIONAL, WITNESS = None, None  # EDIT: for 'kernel', the Lean texts of the functional and of a vector it sends to 1
FIELD = 'ℚ'  # EDIT: the scalars of the goal
if KIND == 'span':
    assert VECTORS is not None, 'fill in VECTORS in a copy'
    proof = tactic(span_dimension_proof(VECTORS, FIELD))
elif KIND == 'intersection':
    assert FIRST is not None and SECOND is not None, 'fill in FIRST and SECOND in a copy'
    proof = tactic(intersection_dimension_proof(FIRST, SECOND, FIELD))
elif KIND == 'kernel':
    assert FUNCTIONAL is not None and WITNESS is not None, 'fill in FUNCTIONAL and WITNESS in a copy'
    proof = tactic(
        f'have h := Veriphy.Linear.finrank_ker_add_one ({FUNCTIONAL}) ({WITNESS}) (by simp)\n'
        'simp [Module.finrank_matrix, Module.finrank_fin_fun] at h\n'
        'omega'
    )
else:
    proof = tactic('simp [Module.finrank_tensorProduct, Module.finrank_matrix, Module.finrank_fin_fun]')
