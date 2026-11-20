# Tasks

## 1. Config

- [ ] 1.1 Add the schema, loading and validation of `veriphy.yaml` (D1). Verify with pytest: no file resolves to the `math` pack, an unknown key fails with its line, and a wrong type fails with its path.
- [ ] 1.2 Add packs by name (entry points) and by path, and ship `core` and `math` as `pack.yaml` directories (D2). Verify with pytest: a local fixture pack contributes its tools and levels, and an unknown pack name is an error.
- [ ] 1.3 Add the merge with `null` removal (D3), and `config show` with sources. Verify with pytest on layered fixtures: later values win, `null` removes, and each value names its source.

## 2. Trust and levels

- [ ] 2.1 Add trust classes and the level chain with the checks (D4, D5). Verify with pytest: a branching order, a cycle, an unknown class and a step granting another class's level are each refused with a message naming them.
- [ ] 2.2 Generate the graph vocabulary's levels from the config, and check that the `math` pack matches Lean (D6). Verify with the graph tests, extended with a pack that adds `reproduced`, and with a test that the pack's level names equal `#veriphy_levels`'s.

## 3. Records and integration

- [ ] 3.1 Put the config digest into every step's input digest. Verify with pytest: changing a tool's pin gives a new digest, and changing a comment in `veriphy.yaml` does not.
- [ ] 3.2 Document `veriphy.yaml` in the user guide and run the gate and CI. Verify that every session and job is green.

## Workflow follow-up

- Archive, and release as a minor version.
