# Spec Delta

## MODIFIED Requirements

### Requirement: Linear packaging lemmas
The module `Veriphy.Kit.Linear` SHALL provide the lemmas the emitters use, each with the standard axioms only: the span
of an echelon family, rank bounds from a minor and from a factorisation, and independence from a non-zero minor.

#### Scenario: Axiom audit
- **WHEN** `#print axioms` runs on each lemma
- **THEN** it lists only `propext`, `Classical.choice` and `Quot.sound`
