# Spec Delta

## Purpose

Gives scripts general-purpose algebraic certificates that research arguments need repeatedly: infeasibility of polynomial systems, normal forms of matrices, closed forms of matrix exponentials, and primality. Each certificate is cheap to check in Lean.

## ADDED Requirements

### Requirement: Positivstellensatz certificates
The toolkit SHALL search for and emit real Positivstellensatz certificates `-1 = σ₀ + Σ σᵢ gᵢ + Σ hⱼ fⱼ`, with SOS multipliers `σ` from the exact SOS solver, proving a semialgebraic system infeasible. The proofs use `linear_combination` and `nlinarith` with `sq_nonneg` hints.

#### Scenario: Infeasible real system
- **WHEN** the hypotheses are `x ^ 2 + y ^ 2 < 1` and `x + y ≥ 2` over ℝ and the goal is `False`
- **THEN** a Positivstellensatz certificate is found and the emitted proof closes the goal

### Requirement: Nullstellensatz certificates
The toolkit SHALL search for and emit, from Gröbner bases, Nullstellensatz certificates `1 = Σ gᵢ fᵢ` (a polynomial system over a field has no common zero) and radical membership certificates `pᵏ = Σ gᵢ fᵢ`.

#### Scenario: No common zero
- **WHEN** the hypotheses are `x * y = 1` and `x = 0` and the goal is `False`
- **THEN** the certificate `1 = y * x - (x * y - 1)` is emitted, as `linear_combination y * hx - hxy`

#### Scenario: Radical membership
- **WHEN** the hypotheses are `x ^ 2 = 0` and the goal is `x = 0` over ℝ
- **THEN** the certificate `x² ∈ ⟨x²⟩` with `k = 2` is emitted with `pow_eq_zero_iff`

### Requirement: Matrix normal forms
The toolkit SHALL compute and certify:
- Smith normal forms over ℤ (`U * A * V = D` with `U`, `V` unimodular, proved by explicit inverses);
- Jordan forms over ℚ or a number field (`P⁻¹ * A * P = J`, proved by `A * P = P * J` and an explicit inverse of `P`);
- diagonalizations, as Jordan forms with no nontrivial blocks.

#### Scenario: Smith normal form
- **WHEN** a script computes the Smith form of an explicit integer matrix
- **THEN** it emits proofs of `U * A * V = D`, `U * U' = 1` and `V * V' = 1`

### Requirement: Matrix exponentials
The toolkit SHALL compute closed forms of `exp(t A)` for explicit matrices with Sage. It SHALL emit a Lean proof against mathlib's `NormedSpace.exp`, through a nilpotent truncation when `A` is nilpotent, through a diagonalization or Jordan decomposition otherwise, or through the ODE characterization (`d/dt exp(tA) = A exp(tA)`, `exp(0) = 1`) and uniqueness.

#### Scenario: Lorentz boost
- **WHEN** the goal is that the exponential of rapidity times the boost generator equals the boost matrix with `cosh` and `sinh` entries
- **THEN** a script certifies it, and the proof builds against mathlib's `exp`

### Requirement: Primality certificates
The toolkit SHALL produce Pratt certificates for primes beyond the reach of `norm_num`'s primality extension. They are checked by the verified checker of the scalable-checking capability.

#### Scenario: Prime used in a number-theoretic argument
- **WHEN** a goal needs `Nat.Prime 1000000007`
- **THEN** a Pratt certificate is emitted and checked without `native_decide`

### Requirement: Algebraic recipes
The recipe set SHALL include `infeasibility` (Nullstellensatz and Positivstellensatz), `matrix_normal_form`, `matrix_exponential` and `primality`, each with its tested template.

#### Scenario: Recipe routing
- **WHEN** an agent's goal is `False` from nonlinear real hypotheses that `farkas` cannot refute
- **THEN** the recipe index routes it to `infeasibility`
