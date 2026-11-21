# Recurrences

## When to use

- The hypotheses define a sequence by a **linear recurrence** `a (n + d) = c₀ a n + … + c_{d-1} a (n + d - 1)` and
  `d` initial values, and the goal is a closed form `a n = f n`.
- Sympy's `rsolve` finds the closed form (constant or polynomial coefficients); Lean proves it by strong induction:
  the `d` initial cases by `norm_num`, the step by rewriting with the recurrence and the induction hypothesis, then
  `ring`.
- For a holonomic sequence given only by terms, `guess_recurrence(terms)` guesses a recurrence with the optional
  `ore_algebra` package (`sage -pip install ore_algebra`).

## Template

Copy it to the project's `.veriphy/certificates/recurrence.sage` (or a more specific name), adapt the lines marked
`EDIT`, keep the header, and run it with `sage_run file "<name>.sage"`.

```sage
# name: recurrence
# technique: closed forms of linear recurrences, proved by strong induction
# goal: a n = f n, with hypotheses a (n + d) = c₀ a n + … and the d initial values
# description: Sympy solves the recurrence (ore_algebra guesses holonomic ones); Lean checks it by strong induction.
COEFFICIENTS = None  # EDIT: c₀, …, c_{d-1} with a(n + d) = c₀ a(n) + … + c_{d-1} a(n + d - 1)
INITIAL = None  # EDIT: a(0), …, a(d - 1)
RECURRENCE = 'hrec'  # EDIT: the name of the hypothesis ∀ n, a (n + d) = …
INITIAL_NAMES = ['h0', 'h1']  # EDIT: the names of the hypotheses a 0 = …, a 1 = …
assert COEFFICIENTS is not None, 'fill in COEFFICIENTS and INITIAL in a copy'
print('closed form:', solve_recurrence(COEFFICIENTS, INITIAL))
proof = recurrence_proof(len(COEFFICIENTS), RECURRENCE, INITIAL_NAMES)
```

## Worked example

```lean
-- with COEFFICIENTS = [-6, 5] and INITIAL = [0, 1]: sympy finds 3^n - 2^n
example (a : ℕ → ℤ) (h0 : a 0 = 0) (h1 : a 1 = 1) (hrec : ∀ n, a (n + 2) = 5 * a (n + 1) - 6 * a n) (n : ℕ) :
    a n = 3 ^ n - 2 ^ n := by
  sage_run file "fibonacci_like.sage"
```

## Failure modes

- **"fill in COEFFICIENTS and INITIAL":** copy the template and fill them in.
- **"no closed form for the recurrence":** sympy found none; guess one (`guess_recurrence`) or prove a weaker statement.
- **"guessing a holonomic recurrence needs the ore_algebra package: sage -pip install ore_algebra":** install it.
- **An unsolved step after `ring`:** the closed form is wrong, or the hypothesis names (`RECURRENCE`,
  `INITIAL_NAMES`) do not match the goal's.
