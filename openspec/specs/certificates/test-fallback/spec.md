# certificates/test-fallback Specification

## Purpose
Checks a claim for which no certificate can be built, by testing its formal statement at instances: the Lean kernel
checks each instance by computation alone, and Sage evaluates the instances Lean cannot state. Every result carries its
level, so a test is never presented as a proof.

## Requirements

### Requirement: Verification levels
Every Veriphy check SHALL carry one of three levels, in this order: `certificate` (a recipe's data, a kernel-checked
proof of the claim), `kernel-test` (the kernel checked the claim at instances, each by computation alone) and
`oracle-test` (Sage evaluated the claim at instances, in exact or interval arithmetic). A claim SHALL be given the
highest feasible level, and the fallback SHALL apply only when no recipe applies.

#### Scenario: A recipe exists
- **WHEN** the goal is `Matrix.rank !![(1 : ℚ), 2, 3; 2, 4, 6] = 1` and the `matrix_rank` recipe closes it
- **THEN** the claim's level is `certificate`, and `sage_test` is not used

#### Scenario: No certificate is feasible
- **WHEN** the claim is rank-nullity for an arbitrary `A : Matrix (Fin m) (Fin n) ℚ`
- **THEN** its proof is a mathlib proof, and its Veriphy check is a `sage_test` at level `kernel-test`

### Requirement: The sage_test command
The system SHALL provide the command `sage_test <constant> file "<name>.sage"` (and the inline form with a script
string). The constant's type SHALL be a proposition, or the constant SHALL be a definition of type `Prop`. Lean SHALL
open its universal binders, serialize the binders and the body as a problem, and run the script, which assigns
`instances`: for each instance, a value for every binder as Lean text, and either a `proof` tactic block or an `oracle`
verdict with its evaluation.

#### Scenario: Kernel-checked instances
- **WHEN** `sage_test rank_nullity file "rank_nullity_test.sage"` runs and the script returns three matrices with
  proofs by `matrix_rank` and `dimension`
- **THEN** Lean instantiates the statement at each matrix, checks each block, and reports the three instances as
  accepted

#### Scenario: A proposition without a proof
- **WHEN** the target is `def sylvester_invariance : Prop := …`, which has no Lean proof
- **THEN** `sage_test` checks its instances the same way, and the level is `kernel-test` or `oracle-test`

### Requirement: Instances are independent of the claim
An instance SHALL be accepted only when its block closes the instantiated goal with the standard axioms and its proof
term does not depend on the target constant, directly or through declarations of the current module.

#### Scenario: Circular instance
- **WHEN** an instance's block is `exact rank_nullity _`
- **THEN** the instance is rejected with a message naming the dependence on `rank_nullity`

### Requirement: Enough instances, including an edge case
A run SHALL need at least three accepted instances, at least one of them an edge case the template marks (zero, one,
the identity, a singular matrix, a degenerate dimension), or it SHALL fail and list every rejected instance with its
reason.

#### Scenario: Too few instances
- **WHEN** only two instances are accepted
- **THEN** the command fails, lists the rejected instances and their reasons, and emits no replacement

### Requirement: Sage-free replacement of a test
A successful run SHALL emit, as its Sage-free replacement, the accepted kernel instances as `example` commands and the
attribute `veriphy_tested` on the target with the level and the instance counts. The replacement SHALL build without
Sage and SHALL be reported only after every emitted instance was accepted.

#### Scenario: Replay
- **WHEN** the replacement is committed and the project builds with Sage absent
- **THEN** the examples are checked again by the kernel, and the target carries `veriphy_tested` with level
  `kernel-test`

### Requirement: Test record
Every run SHALL write `.veriphy/tests/<target>.json` with the target, its statement, the level, the seed, the Sage
version, the script's hash and every instance (values, kind, verdict). `python -m veriphy.certificates tests` SHALL
list the records with their levels, and `--rerun <target>` SHALL rerun the oracle instances. Oracle evaluations SHALL
use exact arithmetic, or interval arithmetic with at least 53 bits, and SHALL NOT compare floating-point numbers.

#### Scenario: Oracle instance
- **WHEN** an instance cannot be stated in Lean and the script evaluates it in interval arithmetic
- **THEN** the record holds the interval and the precision, and the instance counts toward `oracle-test`

#### Scenario: Floating comparison
- **WHEN** a script's oracle verdict compares two `RDF` values
- **THEN** the run fails and names the instance

### Requirement: Level report
`#veriphy_levels [prefixes]` SHALL list the declarations under the prefixes with their level: `certificate` for
declarations whose proof came from a recipe's replacement, `kernel-test` or `oracle-test` for those carrying
`veriphy_tested`, and `none` otherwise.

#### Scenario: Mixed module
- **WHEN** a module has one certified theorem, one tested theorem and one plain mathlib proof
- **THEN** the report lists the three levels `certificate`, `kernel-test` and `none`

### Requirement: Test fallback recipe
The recipe set SHALL include `test_fallback`, with the recipe format (when to use it, a tested template, a worked
example, failure modes). Its "when to use" SHALL require that recipe selection failed or that the goal quantifies over
a dimension, a space or a function. The template SHALL provide the seeded sampler and the edge cases of D3.

#### Scenario: Template run
- **WHEN** the Lean test suite runs the template on a statement quantified over `n : ℕ` and `A : Matrix (Fin n) (Fin n) ℚ`
- **THEN** it accepts at least three instances, one with `n = 0` or a singular `A`
