SCRIPT = {
    'name': 'definite_integral',
    'serves': 'certify',
    'technique': 'fundamental theorem of calculus with an antiderivative from Sage',
    'goal': '∫ x in a..b, f x = v, with f elementary (polynomials, exp, log, sin, cos, sqrt, powers)',
    'description': "Sage finds F with F' = f and checks F b - F a = v; Lean proves HasDerivAt F f and evaluates the bounds.",
    'inputs': {},
}

INDEX = 0  # EDIT: which interval integral of the goal, when it has several


def run(goal, inputs):
    proof = definite_integral_proof(problem, INDEX)
    return found(proof)
