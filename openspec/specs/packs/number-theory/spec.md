# packs/number-theory Specification

## Purpose
TBD - created by archiving change nested-subfields. Update Purpose after archive.

## Requirements

### Requirement: Number-theory pack
Veriphy SHALL ship a `number-theory` pack, nested in `math`, whose steps run PARI under Sage: `check-factorization`
accepts a factorization whose factors multiply to the number and are each proven prime, and `check-class-number`
compares a number field's class number, certified with `bnfcertify`, with the claim, leaving it `undecided` when PARI
cannot certify it. Both SHALL grant `oracle-test`.

#### Scenario: A composite claimed prime
- **WHEN** `check-factorization` claims 2^67 - 1 is its own factorization
- **THEN** it is refused, saying the number is not prime, with PARI's factorization recorded
