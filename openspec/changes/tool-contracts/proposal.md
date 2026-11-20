# Proposal

## Why

A field brings its own tools, and Veriphy should run them the same way it runs SageMath and `oo-horn`: pinned,
seeded and recorded. Today each tool has its own code path and its own environment variables, and only `oo-horn` is
pinned.

## What Changes

- Two tool contracts. **files**: a command reads its inputs and writes a JSON result to a path. **json-lines**: a
  long-running process answers one JSON request per line, as the Sage daemon does.
- A tool entry in the config: `trust`, `contract`, `run` (with `{placeholders}`), `pin`, `seed` and `timeout`.
- Pinning at run time: before a tool runs, Veriphy checks its pin (a container digest, a commit with a hash, or an
  exact version) and records the version it found. A tool that does not match its pin does not run.
- SageMath and `oo-horn` move behind the contracts, declared in the `math` and `core` packs. The Lean bridge takes the
  Sage command from the resolved config, and the environment variables still override it.
- `veriphy.toolkit` stays where it is and is documented as the `math` pack's script library.

Depends on `workspace-config`.

## Capabilities

### New Capabilities

- `core/tool-contracts`: the two contracts, the tool entry, pinning and the adapters for Sage and `oo-horn`.

### Modified Capabilities

None.

## Impact

- New: `veriphy.adapters` (the two contracts, pin checks).
- `veriphy.graph._checker`: `oo-horn` becomes a files tool, with its pinned commit and hash moved to the `core` pack.
- Lean: `Veriphy/Bridge.lean` reads the Sage command from `python -m veriphy config show --tool sage` when present.
