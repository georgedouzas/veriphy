# Tasks

## 1. Contracts

- [ ] 1.1 Add `veriphy.adapters` with the files and json-lines contracts, inputs passed as files or JSON (D1). Verify with pytest on fake tools written as small scripts: a good result, a missing `{out}`, a malformed line, a timeout, and an input with shell syntax that reaches the tool as data.
- [ ] 1.2 Add the three pin kinds and the seed placeholder (D2, D3). Verify with pytest: a matching and a drifting version, a hash mismatch, an image pin without a container runtime reported by `config check`, and a random tool without `seed` refused.

## 2. Sage and oo-horn

- [ ] 2.1 Declare `oo-horn` in the `core` pack and run it through the files contract, keeping first-use setup. Verify with the graph checker tests and the CI integration job's first-use run.
- [ ] 2.2 Declare `sage` in the `math` pack, and have the Lean bridge read its command from the config (D4). Verify with the Lean bridge tests and the integration job, with and without `VERIPHY_SAGE_CMD`.

## 3. Integration

- [ ] 3.1 Document tool entries and contracts, mark `veriphy.toolkit` as the `math` pack's library, and run the gate and CI. Verify that every session and job is green.

## Workflow follow-up

- Archive, and release as a minor version.
