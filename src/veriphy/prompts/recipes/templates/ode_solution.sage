# name: ode_solution
# technique: ODE solution checked by differentiation
# goal: an equation in deriv x with x defined by a hypothesis `hx : x = fun s => …`, or ∃ x, (∀ t, ODE) ∧ conditions
# description: Sage solves (desolve) or takes the stated x; derivative facts, rewriting and ring/field_simp check it.
PROOFS = {}  # EDIT: tactics proving the nonzero conditions no hypothesis states, by their Lean text
SOLUTION = None  # EDIT: a solution body in s_ (e.g. 3 * exp(2 * SR.var('s_'))) when Sage finds none
if problem.exists_function is not None:
    proof = solve_exists(problem, proofs=PROOFS, solution=SOLUTION)
else:
    proof = verify_definition(problem, proofs=PROOFS)
