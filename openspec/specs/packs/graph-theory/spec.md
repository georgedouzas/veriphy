# packs/graph-theory Specification

## Purpose
TBD - created by archiving change nested-subfields. Update Purpose after archive.

## Requirements

### Requirement: Graph-theory pack
Veriphy SHALL ship a `graph-theory` pack, nested in `math`, whose step `check-graph` computes a graph invariant with
Sage, the graph given in graph6 or by a Sage constructor with integer arguments, and compares the claim with it,
granting `oracle-test`.

#### Scenario: The Petersen graph
- **WHEN** a claim says the Petersen graph is Hamiltonian
- **THEN** it is refused with "it is not hamiltonian"; its chromatic number 3 is accepted
