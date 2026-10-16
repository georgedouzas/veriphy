# name: boost_metric
# technique: matrix computation read from the goal, checked entrywise, modulo side relations
# goal: an identity, determinant or trace of explicit matrices or vectors, written in the goal (!![…], ![…], *, ᵀ, *ᵥ, det, trace)
# description: Sage evaluates lhs - rhs from the goal itself; Lean proves it entry by entry or by expanding det or trace.
SIMP = []  # EDIT: extra simp lemmas, for example definitions of named matrices
RELATIONS = ['Real.cosh_sq_sub_sinh_sq']
proof = matrix_from_goal_proof(goal, problem, simp=SIMP, relations=RELATIONS)
