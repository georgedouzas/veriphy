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
