# certificates/procedures Specification

## Purpose
Carries the value that used to live in ready-made certificate tactics: the knowledge of how to build a certificate for a given goal, as procedures, templates and skills that agents and humans follow, proven at least as effective as the tactics they replace.

## Requirements

### Requirement: One recipe per technique
The project SHALL provide one recipe per certificate technique, covering at least ideal membership, Farkas refutation, SOS (factor, hinted, SDP), factorization rewrite, rational witnesses, `nlinarith` hint search, `calc` derivations, case splits, matrix identities and sums by induction. Each recipe SHALL state when to use it, give a fill-in `sage_run` script template, and list its failure modes with the next step for each.

#### Scenario: Recipe for a removed tactic
- **WHEN** a user looks for what replaced `sage_farkas`
- **THEN** the procedures map it to the Farkas recipe, whose template closes the former `sage_farkas` examples

### Requirement: Technique search lives in templates
Technique-specific search (Farkas rows, ideal lifts, product search, witness search, root isolation, closed sums) SHALL be Sage code inside the recipes' templates, built on the toolkit's solvers. It SHALL NOT be a toolkit function.

#### Scenario: Agent adapts a search
- **WHEN** the Farkas template's LP needs an extra constraint for a variant goal
- **THEN** the agent edits the template's Sage code in its own script, with no change to Veriphy

### Requirement: Agent-agnostic and progressively loaded
Recipes SHALL be plain markdown readable by any agent, indexed from the `prove` playbook, and loaded one at a time rather than all at once. A dedicated `certify` skill SHALL guide the build loop: inspect `problem`, choose a recipe, adapt its template, run, read the combined feedback, iterate.

#### Scenario: Agent picks a recipe
- **WHEN** the agent faces an inequality with hypotheses
- **THEN** the playbook's index leads it to the Farkas or hint-search recipe by the stated decision rule, without loading the other recipes

### Requirement: Every template is tested
Each recipe's template, instantiated on its worked example, SHALL be a test in the Lean suite and SHALL pass with replay on.

#### Scenario: Template drift
- **WHEN** a toolkit change breaks a recipe's template
- **THEN** `lake build VeriphyTest` fails on that recipe's example

### Requirement: At least as effective as the removed tactics
Every problem the removed tactics solved (each `sage_*` call in the pre-change test suite) SHALL be solved with `sage_run` following the recipes. A fresh agent given only the skills and procedures, not the removed tactic names, SHALL solve every benchmark problem from its statement, with iterations and wall time recorded per problem.

#### Scenario: Benchmark parity
- **WHEN** the benchmark runs before release
- **THEN** every problem is solved, and the report lists iterations and time per problem

#### Scenario: Regression
- **WHEN** a benchmark problem that the removed tactics solved is not solved
- **THEN** the change is not shippable until a recipe, template or primitive is improved to solve it

### Requirement: Recipes for the extended coverage
The recipe set SHALL include:
- a `derivative` recipe for goals `deriv f a = v`, built on the derivative proof terms;
- `sum_induction` covering sums over `Finset.Icc` and `Finset.Ico` as well as `Finset.range`;
- `transcendental_rewrite` selecting its lemmas from the shared rewrite table, including project entries.

Each SHALL follow the existing recipe format (when to use it, a tested template, a worked example and failure modes).

#### Scenario: Derivative goal
- **WHEN** the goal is `deriv (fun x => x ^ 2 * Real.exp x) 1 = 3 * Real.exp 1`
- **THEN** the `derivative` template closes it, and the replacement builds without Sage

#### Scenario: Interval sum
- **WHEN** the goal is `∑ k ∈ Finset.Icc 1 n, (k : ℚ) = n * (n + 1) / 2`
- **THEN** the `sum_induction` template closes it

#### Scenario: Rewrite from a project entry
- **WHEN** the project's tables add `Real.cosh_sq` for `cosh` and `sinh`, and the goal is `Real.cosh x ^ 2 = Real.sinh x ^ 2 + 1`
- **THEN** the `transcendental_rewrite` template selects that entry without being edited

### Requirement: matrix_from_goal covers the pilot's shapes
The `matrix_from_goal` template SHALL close determinants of `4 × 4` literals, products involving transposes,
identities with symbolic entries, and traces of products. It does so by Laplace expansion, the
`Matrix.mul_apply`/`Matrix.transpose_apply` simp set, a final `ring1`, and the trace simp set.

#### Scenario: Four by four determinant
- **WHEN** the goal is `Matrix.det !![(1 : ℚ), 0, 0, 0; 0, -1, 0, 0; 0, 0, -1, 0; 0, 0, 0, -1] = -1`
- **THEN** the template closes it

#### Scenario: Trace of a product
- **WHEN** the goal is `Matrix.trace (Fᵀ * η * F * η) = 2 * (B ^ 2 - E ^ 2)` for a `4 × 4` field-strength matrix `F` and
  the Minkowski metric `η` (the invariant `F_μν F^μν`; `Matrix.trace (F * Fᵀ)` is the sum of squares `2 * (B ^ 2 + E ^ 2)`)
- **THEN** the template closes it

### Requirement: Identities modulo side relations
`matrix_from_goal` SHALL accept `relations`, a list of Lean lemmas of the form `lhs = rhs`. Sage SHALL reduce each entry
of the goal's difference modulo the relations, and the proof SHALL close each entry by `linear_combination` of the
lemmas with the cofactors Sage found.

#### Scenario: Lorentz boost
- **WHEN** the goal is `Λᵀ * η * Λ = η` with `cosh u` and `sinh u` entries and `relations=['Real.cosh_sq_sub_sinh_sq']`
- **THEN** the template closes it

#### Scenario: Square-root eigenvector
- **WHEN** the goal is `B * !![1; √2; 1] = (2 + √2) • !![1; √2; 1]` with `relations=['Real.sq_sqrt']`
- **THEN** the template closes it, with the condition `0 ≤ 2` discharged

### Requirement: Trigonometric table entries
The core rewrite table SHALL contain the Pythagorean identity, the power-reduction formulas for `cos²` and `sin²`, and
the double- and triple-angle formulas for `sin` and `cos`, so that `transcendental_rewrite` selects them without project
entries.

#### Scenario: Power reduction
- **WHEN** the goal is `Real.cos x ^ 2 = 1 / 2 + 1 / 2 * Real.cos (2 * x)`
- **THEN** `transcendental_rewrite` closes it with the core table

### Requirement: Definite integral recipe
The recipe set SHALL include `definite_integral`, for goals `∫ x in a..b, f x = v` where Sage finds an elementary
antiderivative. The proof SHALL establish `HasDerivAt` of the antiderivative with the `has_deriv_at` emitter, apply
`intervalIntegral.integral_eq_sub_of_hasDerivAt`, and evaluate the endpoints with the rewrite table and `norm_num`.

#### Scenario: Mean of the squared cosine
- **WHEN** the goal is `∫ φ in (0 : ℝ)..(2 * Real.pi), Real.cos φ ^ 2 = Real.pi`
- **THEN** the template closes it with the antiderivative `φ / 2 + Real.sin (2 * φ) / 4`
