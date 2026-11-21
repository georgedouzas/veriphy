# name: matrix_from_goal
# technique: matrix computation read from the goal, checked entrywise, modulo side relations
# goal: an identity, determinant or trace of explicit matrices or vectors, written in the goal (!![…], ![…], *, ᵀ, *ᵥ, det, trace)
# description: Sage evaluates lhs - rhs from the goal itself; Lean proves it entry by entry or by expanding det or trace.
SIMP = []  # EDIT: extra simp lemmas, for example definitions of named matrices
RELATIONS = []  # EDIT: side relations the entries need, as ['Real.cosh_sq_sub_sinh_sq'], ['Real.sq_sqrt']
proof = matrix_from_goal_proof(goal, problem, simp=SIMP, relations=RELATIONS)
