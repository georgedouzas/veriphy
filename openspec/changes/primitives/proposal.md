# Proposal

## Why

Primitives are the bottom layer of the architecture: deterministic, typed operations that a person, a Lean file, a
step or an agent can call, and that every later layer is built from. Today they exist only implicitly. Each tool has
its own code path and environment variables, only `oo-horn` is pinned, nothing can be run by hand outside Lean or an
agent's prompt, and every Lean step starts a fresh process that loads Mathlib again.

## What Changes

- **Primitives.** A primitive is one typed operation, with an input schema, an output schema, a trust class and, when
  it is random, how it takes a seed. It is a Python function, or a method of a tool Veriphy starts.
- **Three ways to run, two of them standard.** `python`: a function called in-process (`module:function`), for
  everything Veriphy can do in its own interpreter. `jsonrpc`: a long-running process speaking JSON-RPC 2.0 over
  stdio, one message per line, for a tool in another interpreter (SageMath). `files`: an external command that reads
  its input file and writes one JSON result, for foreign tools such as R. Inputs never pass through a shell.
- **Checks around every call.** The input is checked against its schema, the tool against its pin (image digest,
  commit with hash, or exact version), and the output against its schema. A mismatch refuses to run.
- **Composites.** A pack's code can compose primitives deterministically. A composite names the part that decides, and
  its trust class is that part's class, or the lowest class of its parts when no part decides.
- **Pure.** A primitive writes no record and reads no workspace config. The same input and seed give the same output.
- **By hand.** `veriphy primitive list`, `describe <primitive>` and `run <primitive> --input <file>`.
- **The first packs, as primitives,** declared in `pack.yaml` and found through the `veriphy.packs` entry point:
  - `core`: `horn.check` (class `checker`) and `shacl.validate` (`measurement`), Python functions;
  - `lean`: `lean.check` (`kernel`), `lean.serialize` and `lean.level`, Python functions driving the community Lean
    REPL, which keeps one environment per import header, so Mathlib loads once;
  - `math`: the Sage daemon as a JSON-RPC tool, each daemon method a `sage.*` primitive, and the composites `meaning`
    and `certify`.
- **The Sage daemon speaks JSON-RPC 2.0.** It still answers the requests of earlier releases, so installed Lean
  libraries keep working, and the Lean bridge sends JSON-RPC 2.0 requests.
- **Today's steps call primitives.** `check`, `level`, `meaning`, `validate` and `reason` keep their records and
  results, and run through primitives.

Every installed pack is available in this change. Selecting packs per workspace comes with `packs-and-config`.

Depends on `operation-api`. The primitives live in `veriphy.primitives` and the packs' `primitives` subpackages
that `layered-modules` created.

## Capabilities

### New Capabilities

- `core/primitives`: primitives, the three ways to run, pins, schemas, composites, purity, the `primitive` command,
  the Lean REPL, and the primitives of the `core`, `lean` and `math` packs.

### Modified Capabilities

None. `veriphy certify`, `#veriphy test` and the step records behave as before; the daemon also answers the old
request format.

## Impact

- New: `veriphy.primitives` (descriptors, contracts, pins, registry, command), the `primitives` subpackages of the
  `core`, `lean` and `math` packs, and their `pack.yaml` declarations.
- `veriphy.steps`, `veriphy.claims`: the Lean and graph steps call primitives.
- The Sage daemon and `Veriphy/Bridge.lean`: JSON-RPC 2.0 messages.
- `pyproject.toml`: `jsonschema` and PyYAML.
- The community Lean REPL, pinned by commit and built against the workspace's toolchain on first use.
