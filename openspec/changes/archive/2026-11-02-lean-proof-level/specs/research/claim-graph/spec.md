# Spec Delta

## MODIFIED Requirements

### Requirement: Veriphy vocabulary
Veriphy SHALL ship one RDF vocabulary for research graphs, in Turtle, with the classes `Claim`, `Convention`,
`Concept` and `Source`, and the properties `uses`, `assumes`, `defines`, `statedIn`, `statement`, `leanName`,
`formalizedBy`, `realizedBy`, `hasLevel`, `conventionFor` and `excludes`. The five levels SHALL be individuals of the
vocabulary, with their order stated as triples.

#### Scenario: Reading the vocabulary
- **WHEN** a user asks the graph API for the vocabulary
- **THEN** it returns the Turtle file, and the file states `none` below `oracle-test` below `kernel-test` below
  `lean-proof` below `certificate`

#### Scenario: A graph with an unknown property
- **WHEN** a source file uses a property in the Veriphy namespace that the vocabulary does not declare
- **THEN** loading the graph fails and names the property and the file
