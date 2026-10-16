# Spec Delta

## ADDED Requirements

### Requirement: Vectors and vector operations
The translation SHALL read `![…]` as a column vector of the matrix form that `matrix_from_goal` reads, and SHALL read
`A *ᵥ v`, `v ᵥ* A`, `v ⬝ᵥ w`, `Matrix.vecMulVec u v` and `Matrix.diagonal v` as matrix products and diagonal matrices
of that form.

#### Scenario: Matrix times vector
- **WHEN** the goal is `!![(1 : ℚ), 2, 3; 2, 4, 6] *ᵥ ![1, 1, -1] = ![0, 0]`
- **THEN** the script sees both sides as explicit matrices, not as opaque atoms

### Requirement: Named matrices
A constant whose definition unfolds to a matrix literal SHALL be read through that literal.

#### Scenario: The Minkowski metric
- **WHEN** the goal contains `KaluzaKlein.Linear.eta`, defined as `!![1, 0, 0, 0; …]`
- **THEN** the script sees the literal entries

### Requirement: Polynomials
`Polynomial K` over a translated field SHALL be read as a polynomial ring with one generator for `Polynomial.X`, with
`Polynomial.derivative`, `Polynomial.eval` and `Polynomial.natDegree` mapped to Sage's.

#### Scenario: Square of a binomial
- **WHEN** the goal is `((X + 1) ^ 2 : ℝ[X]) = 1 + 2 * X + X ^ 2`
- **THEN** the script sees a polynomial identity in one generator, and `ring` closes the emitted proof
