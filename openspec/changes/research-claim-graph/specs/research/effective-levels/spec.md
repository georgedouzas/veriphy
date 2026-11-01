# Spec Delta

## Purpose

Reports, for every claim, its own verification level and a certified cap from the claims it rests on, so a result is
never presented as more verified than its weakest dependency.

## ADDED Requirements

### Requirement: Own level of a claim
A claim's own level SHALL be the level the Lean export gives it, or the level of the Lean claim that formalizes it. A
claim with neither SHALL have the level `none`.

#### Scenario: A prose claim with a formalization
- **WHEN** `eq-3.12` is formalized by `KK.killing_form_value`, whose exported level is `certificate`
- **THEN** the own level of `eq-3.12` is `certificate`, and the report shows the `formalizedBy` triple with its
  provenance

#### Scenario: A prose claim alone
- **WHEN** `eq-4.1` has no formalization
- **THEN** its own level is `none`

### Requirement: Certified level caps
Reasoning SHALL derive that a claim is capped at each level of a claim it uses, directly or transitively, and at every
level above a cap. The effective level of a claim SHALL be the lowest of its own level and its certified caps.

#### Scenario: A theorem on a tested lemma
- **WHEN** `thm-9.1` has own level `certificate` and uses `lemma-8.4`, whose level is `oracle-test`
- **THEN** the effective level of `thm-9.1` is `oracle-test`, and the report names `lemma-8.4` as the claim that caps it

#### Scenario: A dependency without a level
- **WHEN** `thm-9.1` uses `eq-4.1`, whose own level is `none`
- **THEN** the effective level of `thm-9.1` is `none`

### Requirement: Reasoning never raises a level
No rule SHALL derive a level higher than a claim's own level. An effective level SHALL be reported as checked only
when the run that derived its caps was accepted by `oo-horn`, and otherwise as `unchecked`.

#### Scenario: An unchecked cap
- **WHEN** `oo-horn` is missing
- **THEN** the effective levels are shown as `unchecked`, and the own levels are still shown

### Requirement: Level report
The graph CLI SHALL report, per source, each claim with its own level, its effective level, the claim that caps it and
its Lean name, and SHALL summarize how many claims reach each effective level.

#### Scenario: A chapter report
- **WHEN** a user asks for the level report of `chapter9`
- **THEN** the report lists every claim of `chapter9` with the four columns, and ends with the count per effective
  level
