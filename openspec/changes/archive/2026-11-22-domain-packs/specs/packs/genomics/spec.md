## ADDED Requirements

### Requirement: Genomics pack
Veriphy SHALL ship a `genomics` pack, requiring `life-sciences`, whose steps use pysam: `check-variant` checks that a
variant, 1-based, is called in a VCF file, with a sample's genotype, and `check-coverage` recomputes a region's mean
depth from SAM, BAM or CRAM alignments above a mapping quality and compares it with the claim. Both SHALL grant
`genomic-data-checked` (checker), above `sequence-checked`.

#### Scenario: A genotype misreported
- **WHEN** a claim gives the example's control sample genotype 1/1 at chr1:120
- **THEN** it is refused with "control is 0/1, not 1/1"
