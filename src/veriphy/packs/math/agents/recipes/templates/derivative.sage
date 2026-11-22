SCRIPT = {
    'name': 'derivative',
    'serves': 'certify',
    'technique': "derivative at a point, by composed HasDerivAt lemmas, with Sage's value",
    'goal': 'deriv (fun x => f x) a = v, f built from the coverage list (powers, exp, log, sqrt, sin, cos, quotients)',
    'description': "Sage differentiates; mathlib's derivative lemmas, composed, prove HasDerivAt at the point; deriv follows.",
    'inputs': {},
}

PROOFS = {}  # EDIT: tactics proving the nonzero conditions no hypothesis states, by their Lean text


def run(goal, inputs):
    assert problem.derivatives, 'the goal has no derivative Veriphy translates; inspect it with #veriphy translate'
    d = problem.derivatives[0]
    value = diff(d.body, d.var).subs({d.var: d.point})
    assert bool(goal.expr.simplify_full() == 0), f'Sage computes the derivative as {value}, not the stated value'
    proof = steps(
        has_deriv_at_proof(d.body, d.var, d.point, value, problem, proofs=PROOFS, function=d.function, at=d.at),
        tactic('exact hd.deriv.trans (by first | rfl | ring1 | (field_simp; ring1) | norm_num)'),
    )
    return found(proof)
