# Spec Delta

## MODIFIED Requirements

### Requirement: Own level of a claim
A claim's own level SHALL be the highest level granted by a record linked to it: a record whose inputs name the claim
or the Lean declaration that formalizes it, the Lean export included. A claim with no such record SHALL have the level
`none`.

#### Scenario: A prose claim with a formalization
- **WHEN** `eq-3.12` is formalized by `KK.killing_form_value`, whose exported level is `certificate`
- **THEN** the own level of `eq-3.12` is `certificate`, and the report shows the `formalizedBy` triple with its
  provenance

#### Scenario: A prose claim alone
- **WHEN** `eq-4.1` has no formalization and no record
- **THEN** its own level is `none`

#### Scenario: A reproduced claim
- **WHEN** a `reproduce` record naming `est-2` has status `agrees` and grants `reproduced`
- **THEN** the own level of `est-2` is `reproduced`

### Requirement: Level report
The graph CLI SHALL report, per source, each claim with its own level, its effective level, each with its trust
class, the claim that caps it and its Lean name when it has one, and SHALL summarize how many claims reach each
effective level.

#### Scenario: A chapter report
- **WHEN** a user asks for the level report of `chapter9`
- **THEN** the report lists every claim of `chapter9` with its levels and their classes, the capping claim and the
  Lean name, and ends with the count per effective level
