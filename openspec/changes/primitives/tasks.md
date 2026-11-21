# Tasks

## 1. Primitives

- [x] 1.1 Add `veriphy.primitives` with primitive and tool descriptors, JSON Schema checks both ways, and a registry built from the installed packs' `pack.yaml` through the `veriphy.packs` entry point (D1, D6, D8). Verify with pytest on a fixture pack: an invalid input names its field, a drifting output names the missing field, and nothing under `.veriphy/` is read or written.
- [x] 1.2 Add the three ways to run: Python functions in-process, JSON-RPC 2.0 tools over stdio, and files tools, with inputs passed as files or JSON (D2, D3, D4). Verify with pytest on a fixture pack: a function, a JSON-RPC tool and its error object, a malformed line, a files tool's result, a missing `{out}`, a timeout, and an input with shell syntax that reaches the tool as data.
- [x] 1.3 Add the three pin kinds and the seed declaration (D5). Verify with pytest: a matching and a drifting version, a commit pin, an image pin without a container runtime, and the pin kind in every output.
- [x] 1.4 Add composites, with the deciding part and the computed class, and `assert_deterministic` (D7, D8). Verify with pytest: a composite with and without a deciding part gets the expected class, and a seeded primitive passes the determinism helper while an unseeded random one fails it.
- [x] 1.5 Add `veriphy primitive list|describe|run`. Verify with pytest: `run` prints the output and writes no record, and a missing tool is listed as unavailable with its reason.

## 2. Packs

- [x] 2.1 Ship the `core` pack: `horn.check` and `shacl.validate` as Python functions, with `oo-horn`'s pinned commit and hash (D2, D10). Verify with the graph tests, and a test that the pin equals the checker's release.
- [x] 2.2 Ship the `lean` pack: `lean.check`, `lean.serialize` and `lean.level` as Python functions on the pinned REPL, with the file fallback (D9). Verify with pytest, skipped without `lake`: two checks with the same imports load them once, and each output equals `lake env lean`'s on the same file.
- [x] 2.3 Ship the `math` pack: the Sage daemon speaking JSON-RPC 2.0 while answering the old format, a `sage.*` primitive per method, the composites `meaning` and `certify`, and the Lean bridge sending JSON-RPC 2.0 (D3, D7, D10). Verify with a test that every daemon method has a primitive, the oracle tests in both formats, the Lean bridge tests, and a test that the bridge's default command equals the pack's.

## 3. Integration

- [x] 3.1 Move `check`, `level`, `meaning`, `validate` and `reason` onto primitives. Verify with the step tests unchanged.
- [ ] 3.2 Document primitives, the three ways to run and the `primitive` command in the user guide and the architecture page, and run the gate and CI. Verify that every session and job is green.

## Workflow follow-up

- Archive, and release as a minor version.
