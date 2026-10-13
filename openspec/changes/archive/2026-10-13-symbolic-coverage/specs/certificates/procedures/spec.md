# Spec Delta

## ADDED Requirements

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
