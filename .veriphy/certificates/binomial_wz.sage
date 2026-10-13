# name: binomial_wz
# technique: Wilf-Zeilberger pairs and Gosper antidifferences, with telescoping and induction proofs
# goal: ∑ k ∈ Finset.range (n + 1), F n k = S n (a hypergeometric F), or ∑ k ∈ Finset.range n, f k = S n
# description: Sympy's Gosper algorithm finds the certificate; Lean checks the summand identity and telescopes.
import sympy as sp
from veriphy.toolkit._summation import N as n, K as k
SUMMAND = sp.binomial(n, k)
CLOSED_FORM = 2**n
CLOSED_FORM_LEAN = '(2 : ℚ) ^ n'
assert SUMMAND is not None, 'fill in SUMMAND (and CLOSED_FORM, CLOSED_FORM_LEAN for a definite sum) in a copy'
if CLOSED_FORM_LEAN is None:
    print('closed form:', sp.combsimp(gosper_closed_form(SUMMAND)))
    proof = gosper_proof()
else:
    print('WZ mate:', wz_mate(sp.combsimp(SUMMAND / CLOSED_FORM)))
    proof = wz_proof(SUMMAND, CLOSED_FORM, CLOSED_FORM_LEAN)
