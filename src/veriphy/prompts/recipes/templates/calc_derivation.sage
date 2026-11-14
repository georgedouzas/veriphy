# name: calc_derivation
# technique: calc derivation (each step checked on its own)
# goal: lhs = rhs (or ≤ / <) reached through intermediate expressions Sage computes
# description: Chain intermediate forms from Sage; each calc step closes by its own tactic, so a failure names the step.
start = lhs.text  # EDIT: the goal's left side, or a rewritten form of it
middle = expand(SR(str(lhs.poly)))  # EDIT: any intermediate Sage computes (expanded, factored, substituted, ...)
chain = [
    ('=', R(str(middle)), tactic('ring')),  # EDIT: one step per intermediate, each with its own tactic
    ('=', term(rhs.text), tactic('ring')),
]
proof = calc_chain(term(start), chain, problem)
