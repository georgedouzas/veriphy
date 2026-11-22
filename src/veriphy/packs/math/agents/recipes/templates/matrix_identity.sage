SCRIPT = {
    'name': 'matrix_identity',
    'serves': 'certify',
    'technique': 'matrix identity, checked entrywise',
    'goal': 'an identity between explicit matrices (sums, products, transposes)',
    'description': 'Check the identity exactly in Sage first; Lean then proves it entry by entry.',
    'inputs': {},
}

A = matrix(QQ, [[0, 1], [1, 0]])   # EDIT: the matrices of the goal
B = matrix(QQ, [[1, 0], [0, -1]])


def run(goal, inputs):
    assert A * B + B * A == 0, 'the identity is false'   # EDIT: the identity
    proof = tactic('ext i j\nfin_cases i <;> fin_cases j <;> simp')  # entrywise; add simp lemmas if needed
    return found(proof)
