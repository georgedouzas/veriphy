# Proposal

## Why

Primitives are the bottom layer of the architecture: deterministic, typed operations that a person, a Lean file, a
step or an agent can call, and that every later layer is built from. Today they exist only implicitly. Each tool has
its own code path and environment variables, only `oo-horn` is pinned, nothing can be run by hand outside Lean or an
agent's prompt, and every Lean step starts a fresh process that loads Mathlib again.

## What Changes

- **Tools and primitives.** A tool is a program Veriphy starts, with a contract, a command and a pin. A primitive is
  one typed operation on a tool, with an input schema, an output schema, a trust class and, when it is random, how
  it takes a seed.
- **Two contracts.** `files` (read input files, write one JSON result to `{out}`) and `json-lines` (a long-running
  process answering one JSON request per line). Inputs are never interpolated into a shell command.
- **Checks around every call.** The input is checked against its schema, the tool against its pin (image digest,
  commit with hash, or exact version), and the output against its schema. A mismatch refuses to run.
- **Composites.** A pack's code can compose primitives deterministically. A composite names the part that decides, and
  its trust class is that part's class, or the lowest class of its parts when no part decides.
- **Pure.** A primitive writes no record and reads no workspace config. The same input and seed give the same output.
- **By hand.** `python -m veriphy primitive list`, `describe <primitive>` and `run <primitive> --input <file>`.
- **The first packs, as primitives.** Veriphy ships three pack directories with a `pack.yaml` holding `tools` and
  `primitives`, found through the `veriphy.packs` entry point:
  - `core`: `oo-horn.check` (class `checker`) and `shacl.validate` (`measurement`);
  - `lean`: the Lean session tool, and `lean.check` (`kernel`), `lean.serialize` and `lean.levels`;
  - `math`: the Sage daemon, each daemon method as a `sage.*` primitive, and the composites `meaning` and `certify`.
- **A Lean session.** The `lean` tool is a json-lines process that loads a file's imports once and answers many
  requests, so Lean primitives stop paying for Mathlib on every call.
- **Today's steps call primitives.** `elaborate`, `level`, `meaning`, `validate` and `reason` keep their records and
  results, and run through primitives. The Lean bridge takes the Sage command from the `math` pack, and the
  environment variables still override it.

Every installed pack is available in this change. Selecting packs per workspace comes with `packs-and-config`.

Depends on `step-records` and `meaning-step`.

## Capabilities

### New Capabilities

- `core/primitives`: tools, primitives, the two contracts, pins, schemas, composites, purity, the `primitive`
  command, the Lean session and the primitives of the `core`, `lean` and `math` packs.

### Modified Capabilities

None. The daemon's protocol, `sage_run`, `sage_test` and the step records behave as before.

## Impact

- New: `veriphy.primitives` (descriptors, contracts, pins, registry, command), and
  `veriphy/packs/{core,lean,math}/pack.yaml` with their schemas.
- `veriphy.steps`: the Lean and graph steps call primitives instead of `lake env lean` and the checker directly.
- `veriphy.graph._checker`: `oo-horn` becomes a `files` tool, its pinned commit and hash moved to the `core` pack.
- Lean: `Veriphy/Bridge.lean` reads the Sage command from the `math` pack when present.
- `pyproject.toml`: the `veriphy.packs` entry points; `jsonschema` as a dependency.
- A pinned Lean REPL for the `lean` session tool.
