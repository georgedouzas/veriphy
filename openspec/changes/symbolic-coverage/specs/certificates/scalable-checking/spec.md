# Spec Delta

## Purpose

Lets Lean check certificates of research size (248×248 matrices, structure-constant tables with thousands of entries, long Pratt chains, large polynomial identities) by kernel evaluation of checkers proved correct once in Lean. Entrywise `simp` and `norm_num` cannot scale to these sizes.

## ADDED Requirements

### Requirement: Verified reflective checkers
Veriphy SHALL provide Lean checkers over computable data representations:
- sparse rational matrices, with product, sum, commutator, trace and equality;
- sparse multivariate polynomials over ℚ, with equality after normalization;
- structure-constant tables, with the Jacobi identity and the bracket of basis elements;
- Pratt certificates, for primality.

#### Scenario: Structure-constant table
- **WHEN** a script certifies the Jacobi identity for a 52-dimensional structure-constant table
- **THEN** the check runs through the table checker, not through entrywise rewriting

### Requirement: Soundness and kernel evaluation
Each checker SHALL come with a Lean theorem that a `true` result implies the corresponding mathlib statement (matrix equality, polynomial equality, `LieRing` identities, `Nat.Prime`). The check SHALL run by `decide` or `rfl` in the kernel, never by `native_decide`, and the axiom guard SHALL accept the resulting proofs.

#### Scenario: Large matrix identity
- **WHEN** a script certifies that two explicit 64×64 rational matrices commute
- **THEN** the emitted proof applies the soundness theorem of the sparse-matrix checker to a `decide` result, and builds without Sage within the time limits of the Lean suite

#### Scenario: Large prime
- **WHEN** the goal is `Nat.Prime p` for a 40-digit `p`
- **THEN** a Pratt certificate found by Sage is checked by the verified checker, and the proof uses only the standard axioms

### Requirement: Bridge to mathlib statements
The emitters SHALL produce, from a mathlib-level goal (a `Matrix` equality, a polynomial identity, a bracket identity, a primality goal), the reflection step that reduces it to a checker call. This needs the translation from the goal's terms to the checker's data, and a proof that the translation is faithful, by `simp` lemmas on the representation. A goal whose terms cannot be reflected SHALL fall back to the entrywise emitters, and the fallback SHALL be reported.

#### Scenario: Reflected matrix goal
- **WHEN** the goal is `A * B = B * A` with `A` and `B` given as `!![…]` literals
- **THEN** the emitted proof rewrites both sides into the sparse representation and closes the goal with the checker

### Requirement: Size thresholds
The toolkit SHALL choose reflection over entrywise proofs above a size threshold (matrix dimension or term count), configurable by the script. Recipes SHALL document the threshold and how to override it.

#### Scenario: Small goal stays readable
- **WHEN** a 2×2 matrix identity is certified
- **THEN** the emitted proof is the entrywise `ext … norm_num` form, readable in the committed file

### Requirement: Checkers depend on mathlib only
The checkers and their soundness theorems SHALL form a Lean library, `VeriphyCheck`, that imports mathlib only: no Sage bridge, no tactic code. A proof using a checker therefore builds without Sage. The library SHALL also be offered as a single file that a project copies into `.veriphy/lean/`, so that proofs contributed to mathlib or Physlib carry no dependency on Veriphy. The emitted replacement SHALL state which checker module it needs.

#### Scenario: Proof contributed upstream
- **WHEN** a replacement using the sparse-matrix checker is moved into a Physlib file
- **THEN** it builds after copying the checker file, with no Veriphy requirement in Physlib's lakefile
