# Spec Delta

## MODIFIED Requirements

### Requirement: Veriphy vocabulary
Veriphy SHALL ship one RDF vocabulary for research graphs, in Turtle, with the classes `Claim`, `Convention`,
`Concept` and `Source`, and the properties `uses`, `assumes`, `defines`, `statedIn`, `statement`, `leanName`,
`formalizedBy`, `realizedBy`, `hasLevel`, `conventionFor` and `excludes`. The levels of the resolved config SHALL be
individuals of the vocabulary, each with its trust class, and their order SHALL be stated as triples.

#### Scenario: Reading the vocabulary
- **WHEN** a user asks the graph API for the vocabulary in a workspace with the default config
- **THEN** it returns the Turtle, and it states `none` below `oracle-test` below `kernel-test` below `lean-proof`
  below `certificate`

#### Scenario: A pack's levels
- **WHEN** the resolved config places `reproduced` and `robust` between `oracle-test` and `kernel-test`
- **THEN** the vocabulary holds `reproduced` with its class and its place in the order

#### Scenario: A graph with an unknown property
- **WHEN** a source file uses a property in the Veriphy namespace that the vocabulary does not declare
- **THEN** loading the graph fails and names the property and the file
