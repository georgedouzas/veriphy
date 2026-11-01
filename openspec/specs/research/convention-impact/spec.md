# research/convention-impact Specification

## Purpose
Shows which claims a convention reaches and what an edit to the graph changes, before the edit is kept, with each
consequence checked by the certified reasoning.

## Requirements

### Requirement: Claims affected by a convention
The graph CLI SHALL list, for a convention, every claim that assumes it, directly or through its dependencies, grouped
by source. Each entry SHALL give the chain of `uses` through which the claim reaches the convention.

#### Scenario: Normalization of the Killing form
- **WHEN** a user asks for the impact of `killing-normalization-half`, which `lemma-5.2` assumes, and `eq-7.3` uses
  `lemma-5.2`
- **THEN** the list holds `lemma-5.2` with an empty chain and `eq-7.3` with the chain `eq-7.3 → lemma-5.2`

#### Scenario: Unchecked impact
- **WHEN** the run behind the list was not accepted by `oo-horn`
- **THEN** the list is printed under the word `unchecked`

### Requirement: Plan of a graph edit
The graph CLI SHALL compare the graph in the working tree with the graph at a git revision, and report the
consequences the edit adds and removes: `assumes` triples, level caps and clashes. Both sides SHALL be reasoned and
checked.

#### Scenario: Switching a convention
- **WHEN** a user replaces `assumes mostly-minus` with `assumes mostly-plus` on `def-2.1` and asks for the plan against
  `HEAD`
- **THEN** the plan lists every claim that loses `assumes mostly-minus` and gains `assumes mostly-plus`, and every
  clash the edit creates or removes

#### Scenario: An edit with no consequences
- **WHEN** an edit only changes the `statement` text of a claim
- **THEN** the plan reports one changed assertion and no changed consequence

### Requirement: Impact on formalized claims
The impact list and the plan SHALL mark each affected claim that has a Lean name, so a user sees which Lean
declarations to revisit.

#### Scenario: A formalized claim in the impact
- **WHEN** an affected claim is formalized by `KK.coset_curvature`
- **THEN** its entry shows `KK.coset_curvature` and its level
