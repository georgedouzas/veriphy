## ADDED Requirements

### Requirement: Reported numbers
A number input SHALL keep the text it was given, so that `tolerance: reported` is half a unit in the digit it was
reported to, in scientific notation too, and a step's output SHALL show numbers to six significant digits.

#### Scenario: Trailing zeros
- **WHEN** a step compares with `tolerance: reported` and the claim is given as `0.080`
- **THEN** the tolerance is 0.0005, and for `6.674e-11` it is 5e-15

### Requirement: Concepts against a thesaurus or an ontology
Every workspace SHALL have `check-concepts <file>`, which checks that every `vp:Concept` of the claim graph is linked
by `owl:sameAs` to a concept of the file, a SKOS thesaurus or an OBO or OWL ontology read with pronto, reporting each
concept's label, `conforms` when all are defined and a violation naming each one that isn't, and granting no level.

#### Scenario: A Gene Ontology term
- **WHEN** a concept names `GO_0008218` and the file is an OBO excerpt defining it
- **THEN** the status is `conforms`, with the label "bioluminescence"
