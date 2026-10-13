# Root isolation

## When to use

- The goal locates a real root of an explicit polynomial: `∃! x : ℝ, (a < x ∧ x < b) ∧ p x = 0` (or the existence
  part), or an eigenvalue of an explicit 3 by 3 matrix: `∃ x, (a < x ∧ x < b) ∧ (x • 1 - M).det = 0`.
- Sage isolates the roots (`isolate_roots(p)`: rational intervals with opposite signs at the ends and no critical
  point inside). Lean proves existence by the intermediate value theorem with the endpoint signs, and uniqueness by
  strict monotonicity: the derivative's sign on the interval, which `nlinarith` checks. `eigenvalue_proof` expands
  the determinant into the characteristic polynomial first.

## Template

Copy it to the project's `.veriphy/certificates/root_isolation.sage` (or a more specific name), adapt the lines
marked `EDIT`, keep the header, and run it with `sage_run file "<name>.sage"`.

```sage
# name: root_isolation
# technique: isolated real roots by sign changes and monotonicity; eigenvalues through the characteristic polynomial
# goal: ∃! x : ℝ, (a < x ∧ x < b) ∧ p x = 0, or an eigenvalue of an explicit 3 by 3 matrix in an interval
# description: Sage isolates the roots; Lean applies the intermediate value theorem and strict monotonicity.
POLYNOMIAL = None  # EDIT: the polynomial (Sage), e.g. x**3 - 2*x - 1 with x = polygen(QQ, 'x')
POLYNOMIAL_LEAN = None  # EDIT: the polynomial as the goal writes it in x, e.g. 'x ^ 3 - 2 * x - 1'
INTERVAL = None  # EDIT: (a, b) from the goal; None prints the isolating intervals and stops
assert POLYNOMIAL is not None, 'fill in POLYNOMIAL and POLYNOMIAL_LEAN in a copy'
if INTERVAL is None:
    raise AssertionError(f'isolating intervals: {isolate_roots(POLYNOMIAL)}; state the goal on one and set INTERVAL')
proof = root_proof(POLYNOMIAL_LEAN, INTERVAL[0], INTERVAL[1], POLYNOMIAL)
```

## Worked example

```lean
-- with POLYNOMIAL = x**3 - 2*x - 1, POLYNOMIAL_LEAN = 'x ^ 3 - 2 * x - 1' and INTERVAL = (3/2, 3)
example : ∃! x : ℝ, (3 / 2 < x ∧ x < 3) ∧ x ^ 3 - 2 * x - 1 = 0 := by
  sage_run file "golden_root.sage"
```

`VeriphyTest/SageRun.lean` also certifies the largest eigenvalue of a symmetric 3 by 3 matrix in `(3, 4)`.

## Failure modes

- **"isolating intervals: …":** the template prints the intervals; state the goal on one and set `INTERVAL`.
- **"do not have opposite signs":** the interval holds no simple root (or an even number of roots); use an
  interval from `isolate_roots`.
- **"p' vanishes in the interval":** monotonicity fails; split the interval.
- **`nlinarith` leaves the derivative's sign open:** the derivative is close to zero on the interval; narrow it.
