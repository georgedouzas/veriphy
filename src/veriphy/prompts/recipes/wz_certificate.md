# WZ certificates and Gosper sums

## When to use

- The goal is a closed form of a **hypergeometric sum**: `∑ k ∈ Finset.range (n + 1), F n k = S n` with `F` built from
  binomials, factorials and powers (definite, natural boundaries: `F n k = 0` for `k > n`), or
  `∑ k ∈ Finset.range n, f k = S n` (indefinite).
- Definite sums get a **WZ pair**: for the normalized `F / S`, Gosper's algorithm finds the mate `G` with
  `F(n + 1, k) - F(n, k) = G(n, k + 1) - G(n, k)`, as a hypergeometric term with shifted binomials (zero below the
  shift). Lean proves the summand identity (`Nat.choose_succ_succ'`, `field_simp`, `ring`), telescopes it with
  `Finset.sum_range_sub`, and concludes by induction that the normalized sum is 1.
- Indefinite sums get a **Gosper antidifference**: Sage finds `S`, and Lean proves the closed form by induction.
- Use `sum_induction` when the closed form is a polynomial you can guess by evaluation; use this recipe when the
  summand is hypergeometric.

## Template

Copy it to the project's `.veriphy/certificates/wz_certificate.sage` (or a more specific name), adapt the lines
marked `EDIT`, keep the header, and run it with `sage_run file "<name>.sage"`.

```sage
# name: wz_certificate
# technique: Wilf-Zeilberger pairs and Gosper antidifferences, with telescoping and induction proofs
# goal: ∑ k ∈ Finset.range (n + 1), F n k = S n (a hypergeometric F), or ∑ k ∈ Finset.range n, f k = S n
# description: Sympy's Gosper algorithm finds the certificate; Lean checks the summand identity and telescopes.
import sympy as sp
from veriphy.toolkit._summation import N as n, K as k
SUMMAND = None  # EDIT: the summand in n, k (sympy: sp.binomial(n, k), sp.factorial(k), 2**n, …)
CLOSED_FORM = None  # EDIT: S(n) (sympy), for a definite sum over k ≤ n
CLOSED_FORM_LEAN = None  # EDIT: S n as the goal writes it in Lean, e.g. '(2 : ℚ) ^ n'; None for an indefinite sum
assert SUMMAND is not None, 'fill in SUMMAND (and CLOSED_FORM, CLOSED_FORM_LEAN for a definite sum) in a copy'
if CLOSED_FORM_LEAN is None:
    print('closed form:', sp.combsimp(gosper_closed_form(SUMMAND)))
    proof = gosper_proof()
else:
    print('WZ mate:', wz_mate(sp.combsimp(SUMMAND / CLOSED_FORM)))
    proof = wz_proof(SUMMAND, CLOSED_FORM, CLOSED_FORM_LEAN)
```

## Worked examples

```lean
-- with SUMMAND = sp.binomial(n, k), CLOSED_FORM = 2**n and CLOSED_FORM_LEAN = '(2 : ℚ) ^ n'
example (n : ℕ) : ∑ k ∈ Finset.range (n + 1), (n.choose k : ℚ) = 2 ^ n := by
  sage_run file "binomial_wz.sage"

-- with SUMMAND = k * sp.factorial(k) (an indefinite sum: Gosper finds n! - 1)
example (n : ℕ) : ∑ k ∈ Finset.range n, (k * k.factorial : ℚ) = n.factorial - 1 := by
  sage_run file "gosper_factorial.sage"
```

## Failure modes

- **"not Gosper-summable in k: no WZ pair":** the sum has no WZ pair with this normalization; check the closed form
  (a wrong `S` has none), or find a recurrence in `n` with Zeilberger's algorithm (the `recurrence` recipe).
- **"not Gosper-summable: no hypergeometric closed form":** the indefinite sum has no hypergeometric closed form.
- **An unsolved summand identity:** the mate's denominators need a nonzero condition on the range (`n + 1 - k ≠ 0`);
  state it, or rewrite the binomials with `Nat.choose_symm_diff` first.
- **Boundaries:** the definite proof needs `F n k = 0` for `k = n + 1`; sums over other ranges need reindexing first.
