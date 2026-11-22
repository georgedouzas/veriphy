SCRIPT = {
    'name': 'certified_bound',
    'serves': 'certify',
    'technique': "rational bounds on transcendental values from mathlib's decimal lemmas or truncated series",
    'goal': 'Real.exp c < b, b < Real.pi, Real.log c < b and the like, for explicit rationals c and b',
    'description': "Sage's interval arithmetic picks the lemma or the truncation order; Lean checks the rational remainder.",
    'inputs': {},
}

import re


def run(goal, inputs):
    text = goal.text if goal is not None else ''
    matched = re.search(r'Real\.(\w+)\s*\(?\s*([-0-9./ ]*?)\s*\)?\s*(<|>)\s*([0-9.]+)$', text) or \
        re.search(r'^([0-9.]+)\s*(<|>)\s*Real\.(\w+)\s*\(?\s*([-0-9./ ]*?)\s*\)?$', text)
    assert matched, f'the goal must compare Real.f c with a decimal: {text}'
    if text.startswith('Real.'):
        function, point, relation, bound = matched.groups()
        upper = relation == '<'
    else:
        bound, relation, function, point = matched.groups()
        upper = relation == '>'
    point = QQ(sage_eval(point)) if point.strip() else QQ(0)
    proof = bound_proof(function.lower(), point, QQ(Integer(bound.replace('.', ''))) / 10 ** len(bound.partition('.')[2]), upper=upper)
    return found(proof)
