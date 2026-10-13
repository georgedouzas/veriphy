# certificates/symbolic-translation Specification

## Purpose
Gives proof scripts the full mathematical structure of a goal and its hypotheses as Sage symbolic expressions, together with the side conditions Lean will need to check a proof built from them.

## Requirements

### Requirement: Symbolic form of every translatable constraint
Each hypothesis and goal SHALL carry a Sage symbolic-ring expression whenever its terms translate, in addition to the polynomial form it carries when it is polynomial. Subterms that do not translate SHALL become atoms, as for polynomial forms.

#### Scenario: Rational function
- **WHEN** the goal is `x / (x ^ 2 + 1) ≤ 1 / 2` over ℝ
- **THEN** the script sees the goal's symbolic form `x0/(x0^2 + 1) - 1/2` with relation `le`, and no polynomial form

#### Scenario: Transcendental identity
- **WHEN** the goal is `Real.exp a * Real.exp b = Real.exp (a + b)`
- **THEN** the script sees `exp(x0)*exp(x1) - exp(x0 + x1)` with relation `eq`, where `x0` and `x1` are the atoms `a` and `b`, not `Real.exp a` and `Real.exp b`

### Requirement: Translation coverage
The translation SHALL cover the field operations, powers with numeral or symbolic exponents, `|·|` and `%`; `Real` and `Complex` `sqrt`, `exp`, `log`, `sin`, `cos` and `tan`, and the constants `π`, `e` and `Complex.I`; `Real.rpow`, the hyperbolic and inverse trigonometric functions, and `Real.logb`; numerals and casts between ℕ, ℤ, ℚ, ℝ and ℂ; factorials, binomials, `gcd`, `floor` and `ceil`, and division and remainder on ℕ and ℤ; and every entry of the project's translation tables.

#### Scenario: Integer functions
- **WHEN** the goal contains `Nat.choose n 2 * Nat.factorial 2`
- **THEN** the script sees `binomial(n, 2)*factorial(2)` over the atom `n` of type ℕ

### Requirement: Translation of sums, derivatives, matrices and polynomials
The translation SHALL cover sums and products over `Finset.range`, `Finset.Icc` and `Finset.Ico`, with numeral or symbolic bounds, nested to any depth; `deriv` of a lambda whose body is covered, at a covered point; matrix literals with `det`, `trace`, `transpose` and inverse; and `Polynomial` `X`, `C`, `eval`, `coeff` and `degree`.

#### Scenario: Matrix read from the goal
- **WHEN** the goal compares `!![0, 1; 1, 0] * !![1, 0; 0, -1]` with another matrix expression
- **THEN** the script sees both sides as Sage matrices, without the matrices being retyped in the script

#### Scenario: Range sum
- **WHEN** the goal is `∑ k ∈ Finset.range n, (k : ℚ) ^ 2 = F n`
- **THEN** the script sees the left side as the symbolic sum `sum(k^2, k, 0, n - 1)`

#### Scenario: Interval sum with symbolic bounds
- **WHEN** the goal contains `∑ k ∈ Finset.Icc 1 n, (k : ℚ)`
- **THEN** the script sees the symbolic sum `sum(k, k, 1, n)`

#### Scenario: Derivative at a point
- **WHEN** the goal is `deriv (fun x => x ^ 2 * Real.exp x) 1 = 3 * Real.exp 1`
- **THEN** the script sees the left side as Sage's derivative of `x^2*exp(x)` evaluated at `1`

### Requirement: Typed atoms
Every atom SHALL carry its Lean type, one of ℕ, ℤ, ℚ, ℝ, ℂ, a matrix type, or `other`. Scripts SHALL see, for each atom, the facts its type implies: nonnegativity of casts from ℕ, and integrality of casts from ℕ and ℤ.

#### Scenario: Natural-number cast
- **WHEN** an atom is `(n : ℝ)` cast from `n : ℕ`
- **THEN** the script sees its type as ℕ and the fact `0 ≤ ↑n`, which it may use as a hint

### Requirement: Domain conditions
Extraction SHALL list the conditions each symbolic form needs to be meaningful in Lean, each one of `e ≠ 0`, `0 ≤ e`, `0 < e`, or `a ≤ b` between two terms. Each condition SHALL name a hypothesis that states it (or a stronger form of it), or be marked undischarged. For `deriv`, the conditions apply at the point of evaluation, to every subterm that depends on the bound variable.

#### Scenario: Denominator discharged by a hypothesis
- **WHEN** the goal contains `1 / y` and the context has `hy : y ≠ 0`
- **THEN** the condition `y ≠ 0` is listed as discharged by `hy`

#### Scenario: Undischarged condition
- **WHEN** the goal contains `Real.log x` and no hypothesis states `0 < x`
- **THEN** the condition `0 < x` is listed as undischarged, so the script can decide to prove it or to report it

### Requirement: Conditions of each function
The conditions SHALL be: every non-numeral denominator nonzero; every `sqrt` argument nonnegative and every `log` argument positive; every `rpow` base positive (nonnegative when the exponent is a positive numeral); `0 < b`, `b ≠ 1` and `0 < x` for `Real.logb b x`; `arcsin` and `arccos` arguments within `[-1, 1]`; a positive divisor for integer division and remainder; `b ≤ a` for ℕ subtraction `a - b`; and the conditions of each project entry.

#### Scenario: Two-term condition
- **WHEN** the goal contains `n - k` over ℕ and the context has `hk : k ≤ n`
- **THEN** the condition `k ≤ n` is listed as discharged by `hk`

### Requirement: Round-trip fidelity
For every construct in the coverage list, translating a Lean term to Sage and rendering it back with the symbolic emitters SHALL produce a Lean term that is provably equal to the original, by `rfl`, `norm_num` or `ring_nf`.

#### Scenario: Round-trip test suite
- **WHEN** the round-trip tests run over one example per covered construct
- **THEN** each rendered term elaborates and is proved equal to its original

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
