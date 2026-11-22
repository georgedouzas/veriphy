# packs/life-sciences Specification

## Purpose
TBD - created by archiving change domain-packs. Update Purpose after archive.

## Requirements

### Requirement: Life-sciences pack
Veriphy SHALL ship a `life-sciences` pack whose step `check-sequence` reads FASTA with Biopython and checks a record's
claimed length, GC fraction, motif and translation, granting `sequence-checked` (checker), with the conventions
`genome-assembly` and `gene-nomenclature`.

#### Scenario: A wrong length
- **WHEN** `check-sequence` claims 717 bases of the example's 720-base record
- **THEN** it is refused with "the length is 720, not 717"
