# Tasks

## 1. Primitives

- [ ] 1.1 Add `veriphy.primitives` with tool and primitive descriptors, JSON Schema checks both ways, and a registry built from the installed packs' `pack.yaml` through the `veriphy.packs` entry point (D1, D4, D6). Verify with pytest on a fixture pack: an invalid input names its field, a drifting output names the missing field, and nothing under `.veriphy/` is read or written.
- [ ] 1.2 Add the files and json-lines contracts, with inputs passed as files or JSON (D2). Verify with pytest on fake tools written as small scripts: a good result, a missing `{out}`, a malformed line, a timeout, and an input with shell syntax that reaches the tool as data.
- [ ] 1.3 Add the three pin kinds and the seed declaration (D3). Verify with pytest: a matching and a drifting version, a hash mismatch, an image pin without a container runtime, and the pin kind in every output.
- [ ] 1.4 Add composites, with the deciding part and the computed class, and `assert_deterministic` (D5, D6). Verify with pytest: a composite with and without a deciding part gets the expected class, and a seeded fake primitive passes the determinism helper while an unseeded random one fails it.
- [ ] 1.5 Add `veriphy primitive list|describe|run`. Verify with pytest: `run` prints the output and writes no record, and a missing tool is listed as unavailable with its reason.

## 2. Packs

- [ ] 2.1 Ship the `core` pack: `oo-horn` as a files tool with its pinned commit and hash, keeping first-use setup, and `shacl.validate` (D8). Verify with the graph checker tests and the CI integration job's first-use run.
- [ ] 2.2 Ship the `lean` pack: the session tool on the pinned REPL, and `lean.check`, `lean.serialize` and `lean.level` (D7, D8). Verify with pytest, skipped without `lake`: two checks with the same imports load them once, and each output equals `lake env lean --json`'s on the same file.
- [ ] 2.3 Ship the `math` pack: the `sage` tool, a schema and a `sage.*` primitive per daemon method, the composites `meaning` and `certify`, and the Lean bridge reading the Sage command from the pack (D4, D5). Verify with a test that every method in `METHODS` has a primitive, the oracle tests through primitives, and the Lean bridge tests with and without `VERIPHY_SAGE_CMD`.

## 3. Integration

- [ ] 3.1 Move `check`, `level`, `meaning`, `validate` and `reason` onto primitives. Verify with the step tests unchanged, and that the meaning step test runs faster through the session.
- [ ] 3.2 Document primitives, tools, contracts and the `primitive` command in the user guide, and run the gate and CI. Verify that every session and job is green.

## Workflow follow-up

- Archive, and release as a minor version.
