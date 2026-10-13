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
