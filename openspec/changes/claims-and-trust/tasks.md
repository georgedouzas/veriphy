# Tasks

## 1. Classes and levels

- [ ] 1.1 Add the six trust classes to the schema and the level chain to the claims registry, with the checks for unknown classes, branching and cycles (D1, D2). Verify with pytest: an invented class, two levels above one, and a cycle are each refused naming them, and a workspace override settles a branch.
- [ ] 1.2 Declare `none` in `core`, `lean-proof` in `lean`, and `certificate`, `kernel-test` and `oracle-test` in `math`, and remove the fixed lists from the graph package. Verify with the graph tests unchanged, and a test that the packs' level names equal `#veriphy level`'s.

## 2. Granting and claims

- [ ] 2.1 Add the grant rule to `config check` and to the step runner (D3). Verify with pytest: a step granting another class's level is refused by both, and evidence records carry no level.
- [ ] 2.2 Take a claim's own level from linked records, the Lean export as one of them (D4). Verify with the effective-level tests unchanged, and a fixture where a fake `reproduce` record gives a claim `reproduced`.
- [ ] 2.3 Generate the vocabulary's levels from the config and show classes in reports (D5). Verify with the graph tests extended with a pack that adds `reproduced`, and with `packs: [core]` running `reason` and `report`.

## 3. Integration

- [ ] 3.1 Document trust classes and pack levels in the user guide and the research docs, and run the gate and CI. Verify that every session and job is green.

## Workflow follow-up

- Archive, and release as a minor version.
