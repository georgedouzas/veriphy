# Spec Delta

## MODIFIED Requirements

### Requirement: Translation coverage
The translation SHALL cover:
- the field operations, powers with numeral or symbolic exponents, and `|·|` and `%`;
- `Real` and `Complex` `sqrt`, `exp`, `log`, `sin`, `cos` and `tan`, and the constants `π`, `e` and `Complex.I`;
- `Real.rpow` with real exponents, `Real.cosh`, `Real.sinh`, `Real.tanh`, `Real.arctan`, `Real.arcsin`, `Real.arccos` and `Real.logb`;
- numerals and casts between ℕ, ℤ, ℚ, ℝ and ℂ;
- `Nat.factorial`, `Nat.choose`, `Nat.gcd`, `Int.gcd`, `Int.floor`, `Int.ceil`, and division and remainder on ℕ and ℤ;
- sums and products over `Finset.range`, `Finset.Icc` and `Finset.Ico`, with numeral or symbolic bounds, nested to any depth;
- `deriv` of a lambda whose body is in the coverage list, at a point in the coverage list;
- matrix literals and `det`, `trace`, `transpose` and inverse;
- `Polynomial` `X`, `C`, `eval`, `coeff` and `degree`;
- every entry of the project's translation tables.

#### Scenario: Matrix read from the goal
- **WHEN** the goal compares `!![0, 1; 1, 0] * !![1, 0; 0, -1]` with another matrix expression
- **THEN** the script sees both sides as Sage matrices, without the matrices being retyped in the script

#### Scenario: Range sum
- **WHEN** the goal is `∑ k ∈ Finset.range n, (k : ℚ) ^ 2 = F n`
- **THEN** the script sees the left side as the symbolic sum `sum(k^2, k, 0, n - 1)`

#### Scenario: Interval sum with symbolic bounds
- **WHEN** the goal contains `∑ k ∈ Finset.Icc 1 n, (k : ℚ)`
- **THEN** the script sees the symbolic sum `sum(k, k, 1, n)`

#### Scenario: Integer functions
- **WHEN** the goal contains `Nat.choose n 2 * Nat.factorial 2`
- **THEN** the script sees `binomial(n, 2)*factorial(2)` over the atom `n` of type ℕ

#### Scenario: Derivative at a point
- **WHEN** the goal is `deriv (fun x => x ^ 2 * Real.exp x) 1 = 3 * Real.exp 1`
- **THEN** the script sees the left side as Sage's derivative of `x^2*exp(x)` evaluated at `1`

### Requirement: Domain conditions
Extraction SHALL list the conditions each symbolic form needs to be meaningful in Lean. Each condition is one of `e ≠ 0`, `0 ≤ e`, `0 < e`, or `a ≤ b` between two terms. The conditions are:
- every non-numeral denominator nonzero;
- every `sqrt` argument nonnegative, every `log` argument positive;
- every `rpow` base positive (nonnegative when the exponent is a positive numeral);
- `Real.logb b x` needs `0 < b`, `b ≠ 1` and `0 < x`;
- `arcsin` and `arccos` arguments within `[-1, 1]`;
- integer division and remainder need a positive divisor;
- ℕ subtraction `a - b` needs `b ≤ a`;
- the conditions of each project entry;
- for `deriv`, the conditions above at the point of evaluation, for every subterm that depends on the bound variable.

Each condition SHALL name a hypothesis that states it (or a stronger form of it), or be marked undischarged.

#### Scenario: Denominator discharged by a hypothesis
- **WHEN** the goal contains `1 / y` and the context has `hy : y ≠ 0`
- **THEN** the condition `y ≠ 0` is listed as discharged by `hy`

#### Scenario: Undischarged condition
- **WHEN** the goal contains `Real.log x` and no hypothesis states `0 < x`
- **THEN** the condition `0 < x` is listed as undischarged, so the script can decide to prove it or to report it

#### Scenario: Two-term condition
- **WHEN** the goal contains `n - k` over ℕ and the context has `hk : k ≤ n`
- **THEN** the condition `k ≤ n` is listed as discharged by `hk`

## ADDED Requirements

### Requirement: Semantic gaps stay opaque
Where Lean's definition and Sage's disagree and no condition bridges them, the translation SHALL leave the term opaque instead of translating it. These cases are:
- ℕ subtraction with no `b ≤ a` derivable from a hypothesis;
- integer division or remainder by a divisor that is not a positive numeral and has no positivity hypothesis;
- a `deriv` whose body is outside the coverage list.

The opaque term SHALL become an atom with its Lean text, as any untranslated subterm does.

#### Scenario: Truncated subtraction
- **WHEN** the goal contains `n - k` over ℕ and no hypothesis implies `k ≤ n`
- **THEN** `n - k` is one atom, not the Sage expression `n - k`

#### Scenario: Positive numeral divisor
- **WHEN** the goal contains `n / 2` over ℕ
- **THEN** the script sees `floor(n/2)` and no undischarged condition

### Requirement: Typed sub-expressions
The serialized symbolic form SHALL mark where a sub-expression's Lean type changes (a cast from ℕ or ℤ into a field, an `Int.floor` back into ℤ), so the rendering can restore the casts.

#### Scenario: Cast of a remainder
- **WHEN** the goal over ℝ contains `((n % 7 : ℕ) : ℝ)`
- **THEN** the symbolic form records that `n % 7` is computed in ℕ and cast to ℝ
