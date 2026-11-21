# Tasks

## 1. Layers

- [ ] 1.1 Create the layer subpackages and the `core`, `lean` and `math` pack directories, move the record store into `veriphy.steps`, and add step registration (D1, D4). Verify with the step tests, and that `python -m veriphy report` runs through registration.
- [ ] 1.2 Move `oracle`, `sage_server`, `toolkit` and `translations` into `veriphy.packs.math`, add the `veriphy.script` facade, and start the daemon from its new path in the Lean bridge (D1, D5). Verify with the oracle, toolkit and translation tests, and the Lean bridge tests.
- [ ] 1.3 Move `graph` into `veriphy.primitives.graph` (engine, process runner, checker) and `veriphy.claims` (the rest), with the graph steps, and the Lean steps and `certificates` into their packs (D1, D4). Verify with the graph, step and certificate tests.
- [ ] 1.4 Move `prompts` into `veriphy.agents`, with the playbooks and assets in the `math` pack, and update the package data. Verify with the recipe and research document tests, and a wheel build whose contents list the playbooks and assets.

## 2. Rule and aliases

- [ ] 2.1 Add the import-rule test (D3). Verify that it passes on the tree, and fails on a fixture module with an upward import, naming both layers.
- [ ] 2.2 Add the deprecated aliases for every old module and program (D2). Verify with a test that each alias exposes its target's public names and warns once, and that each old `python -m` program runs.

## 3. Integration

- [ ] 3.1 Update the docs, skills and playbooks to the new paths, and run the gate and CI. Verify that every session and job is green, with the Lean test suite built.

## Workflow follow-up

- Archive, and release as a minor version with the operation API.
