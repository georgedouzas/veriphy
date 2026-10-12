# Spec Delta

## Purpose

Gives proof scripts the full mathematical structure of a goal and its hypotheses as Sage symbolic expressions, together with the side conditions Lean will need to check a proof built from them.

## ADDED Requirements

### Requirement: Symbolic form of every translatable constraint
Each hypothesis and goal SHALL carry a Sage symbolic-ring expression whenever its terms translate, in addition to the polynomial form it carries when it is polynomial. Subterms that do not translate SHALL become atoms, as for polynomial forms.

#### Scenario: Rational function
- **WHEN** the goal is `x / (x ^ 2 + 1) ≤ 1 / 2` over ℝ
- **THEN** the script sees the goal's symbolic form `x0/(x0^2 + 1) - 1/2` with relation `le`, and no polynomial form

#### Scenario: Transcendental identity
- **WHEN** the goal is `Real.exp a * Real.exp b = Real.exp (a + b)`
- **THEN** the script sees `exp(x0)*exp(x1) - exp(x0 + x1)` with relation `eq`, where `x0` and `x1` are the atoms `a` and `b`, not `Real.exp a` and `Real.exp b`

### Requirement: Translation coverage
The translation SHALL cover:
- the field operations, powers with numeral or symbolic exponents, and `|·|` and `%`;
- `Real` and `Complex` `sqrt`, `exp`, `log`, `sin`, `cos` and `tan`, and the constants `π`, `e` and `Complex.I`;
- numerals and casts between ℕ, ℤ, ℚ, ℝ and ℂ;
- sums and products over `Finset.range`;
- matrix literals and `det`, `trace`, `transpose` and inverse;
- `Polynomial` `X`, `C`, `eval`, `coeff` and `degree`.

#### Scenario: Matrix read from the goal
- **WHEN** the goal compares `!![0, 1; 1, 0] * !![1, 0; 0, -1]` with another matrix expression
- **THEN** the script sees both sides as Sage matrices, without the matrices being retyped in the script

#### Scenario: Range sum
- **WHEN** the goal is `∑ k ∈ Finset.range n, (k : ℚ) ^ 2 = F n`
- **THEN** the script sees the left side as the symbolic sum `sum(k^2, k, 0, n - 1)`

### Requirement: Typed atoms
Every atom SHALL carry its Lean type, one of ℕ, ℤ, ℚ, ℝ, ℂ, a matrix type, or `other`. Scripts SHALL see, for each atom, the facts its type implies: nonnegativity of casts from ℕ, and integrality of casts from ℕ and ℤ.

#### Scenario: Natural-number cast
- **WHEN** an atom is `(n : ℝ)` cast from `n : ℕ`
- **THEN** the script sees its type as ℕ and the fact `0 ≤ ↑n`, which it may use as a hint

### Requirement: Domain conditions
Extraction SHALL list the conditions each symbolic form needs to be meaningful in Lean: every non-numeral denominator nonzero, every `sqrt` argument nonnegative, every `log` argument positive. Each condition SHALL name a hypothesis that states it, or be marked undischarged.

#### Scenario: Denominator discharged by a hypothesis
- **WHEN** the goal contains `1 / y` and the context has `hy : y ≠ 0`
- **THEN** the condition `y ≠ 0` is listed as discharged by `hy`

#### Scenario: Undischarged condition
- **WHEN** the goal contains `Real.log x` and no hypothesis states `0 < x`
- **THEN** the condition `0 < x` is listed as undischarged, so the script can decide to prove it or to report it

### Requirement: Round-trip fidelity
For every construct in the coverage list, translating a Lean term to Sage and rendering it back with the symbolic emitters SHALL produce a Lean term that is provably equal to the original, by `rfl`, `norm_num` or `ring_nf`.

#### Scenario: Round-trip test suite
- **WHEN** the round-trip tests run over one example per covered construct
- **THEN** each rendered term elaborates and is proved equal to its original
