# certificates/checker-families Specification

## Purpose
Defines the fixed set of kernel-checked proof shapes that certificate tactics close goals with, and the uniform contract by which a tactic runs its check and emits a Sage-free replacement.

## Requirements

### Requirement: Fixed family set
The system SHALL provide exactly these checker families: `identity`, `inequality`, `witness`, `sum` and `cases`. Each family SHALL close goals only through mathlib checkers (`ring1`, `linear_combination`, `positivity`, `norm_num`, induction, `decide`). No family SHALL use `sorry`, an axiom, or an oracle result as a proof term.

#### Scenario: Family list is closed
- **WHEN** a tactic author asks for a family name outside the set
- **THEN** the request is rejected at elaboration time

### Requirement: Identity family
The `identity` family SHALL close a polynomial equality goal in one of two ways. Given a polynomial `F`, it proves `lhs = F` by `ring1` and continues with `F = rhs`. Given cofactors on hypotheses, it closes the goal with `linear_combination Σ cᵢ * hᵢ`.

#### Scenario: Ideal-membership certificate
- **WHEN** the goal is `a ^ 2 + b ^ 2 = 5` with `h : a + b = 3`, `h' : a * b = 2`, and the cofactors are `(a + b + 3)` for `h` and `-2` for `h'`
- **THEN** the goal closes by `linear_combination (a + b + 3) * h - 2 * h'`

#### Scenario: Wrong cofactors
- **WHEN** the supplied cofactors do not make the identity hold
- **THEN** the tactic fails with the checker's error, and the goal is left unchanged

### Requirement: Inequality family
The `inequality` family SHALL close a `≤`/`<` goal, or a `≥`/`>` goal after flipping, with `linear_combination` over weighted hypotheses and `sq_nonneg` terms. It SHALL close a `False` goal, or a negated relation goal, by deriving `κ ≤ 0` or `κ < 0` for a constant `κ` and refuting it with `norm_num`.

#### Scenario: Farkas refutation
- **WHEN** the goal is `False` from `h1 : x + y ≤ 1`, `h2 : x - y = 3`, `h3 : 0 ≤ y`, with certificate weights for each hypothesis
- **THEN** the goal closes through a constant inequality that `norm_num` refutes

#### Scenario: Square-weighted bound
- **WHEN** the goal is `2 * x * y ≤ x ^ 2 + y ^ 2` and the certificate is the single square term `sq_nonneg (x - y)`
- **THEN** the goal closes by `linear_combination sq_nonneg (x - y)`

#### Scenario: Negative weight on an inequality
- **WHEN** a certificate puts weight `-1` on a `≤` hypothesis
- **THEN** the check fails, because positivity cannot certify the weight, and no proof is produced

### Requirement: Witness family
The `witness` family SHALL close an `∃` goal with the supplied values for its binders. Each conjunct of the body SHALL be discharged by `norm_num`.

#### Scenario: Eigenvector witness
- **WHEN** the goal is `∃ v₁ v₂ : ℚ, 2 * v₁ + v₂ = 3 * v₁ ∧ v₁ + 2 * v₂ = 3 * v₂ ∧ v₁ ≠ 0` and the witness is `(1, 1)`
- **THEN** the goal closes by `exact ⟨1, 1, by norm_num⟩`

### Requirement: Sum family
The `sum` family SHALL close `∑ k ∈ Finset.range n, f k = F n` by induction on `n`. Both cases SHALL be discharged by `push_cast` (when needed) and `ring1`, with no oracle data.

#### Scenario: Closed form of squares
- **WHEN** the goal is the sum of `(k : ℚ) ^ 2` over `range n` equals `n ^ 3 / 3 - n ^ 2 / 2 + n / 6`
- **THEN** the goal closes, and the emitted proof contains no reference to Sage

### Requirement: Cases family
The `cases` family SHALL close a decidable goal over a finite domain with `decide`.

#### Scenario: Finite check
- **WHEN** the goal is `∀ x : Fin 4, x * x ≠ 2`
- **THEN** the goal closes by `decide`

### Requirement: Uniform close-and-emit
Every family SHALL run its proof against the current goal and, on success, emit exactly one `Try this:` replacement headed `Sage-free replacement:`. On failure the goal SHALL be unchanged and no suggestion SHALL be emitted.

#### Scenario: Successful close
- **WHEN** any `sage_*` tactic closes its goal through a family
- **THEN** exactly one `Sage-free replacement:` suggestion is attached to the tactic's syntax

#### Scenario: Failed check
- **WHEN** the family's checker rejects the built proof
- **THEN** the tactic errors, the goal list is unchanged, and no suggestion is attached

### Requirement: Existing tactics preserve their interface
`sage_factor`, `sage_sos` (with or without hints), `sage_lincomb`, `sage_witness`, `sage_sum`, `sage_farkas` and `sage_exists` SHALL keep their syntax and the goal shapes they accept. They SHALL close goals and leave residual goals exactly as before. Each one's replacement SHALL be produced by a checker family.

#### Scenario: Existing test file still passes
- **WHEN** `lake build VeriphyTest` runs with the components in place
- **THEN** every pre-existing example in `VeriphyTest.lean` elaborates without edits to its tactic calls
