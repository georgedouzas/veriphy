# packs/group-theory Specification

## Purpose
TBD - created by archiving change nested-subfields. Update Purpose after archive.

## Requirements

### Requirement: Group-theory pack
Veriphy SHALL ship a `group-theory` pack, nested in `math`, whose step `check-group` computes a finite group's order,
structure, identification or a property with GAP under Sage and compares the claim with it, granting `oracle-test`.
A group SHALL be named only by a GAP constructor with integer arguments; anything else fails without being evaluated.

#### Scenario: GAP code as a group
- **WHEN** the group is given as `Exec("ls")`
- **THEN** the status is `failed`, and GAP evaluates nothing
