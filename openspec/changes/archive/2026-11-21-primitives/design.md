# Design

## Context

The Sage daemon answers one JSON request per line in its own format, and the Lean bridge starts it from
`VERIPHY_SAGE_CMD` and `VERIPHY_SAGE_SERVER`. `_checker.py` pins `oo-horn` by commit and SHA-256 and sets it up on first
use. The steps of `step-records` and `meaning-step` run `lake env lean --json` on a generated file, so each Lean step
loads Mathlib again, which costs minutes. The daemon methods take keyword arguments and declare no schema.

## Goals / Non-Goals

**Goals:**

- Every operation Veriphy relies on is a primitive with a schema, a trust class and a pin, callable by hand.
- No protocol of Veriphy's own: what runs in Veriphy's interpreter is a function call, and what runs in another
  speaks JSON-RPC 2.0.
- A Lean primitive costs Mathlib's load once per process, not once per call.

**Non-Goals:**

- Selecting packs per workspace and the `veriphy.yaml` file (`packs-and-config`).
- Declaring steps in YAML (`declarative-steps`). Steps keep their Python definitions and call primitives.
- Levels and the grant rule (`claims-and-trust`). Primitives declare a trust class, and nothing enforces it yet.

## Decisions

### D1. A primitive is a function, a method of a process, or a command

A primitive entry has `trust`, `input`, `output`, `seed`, and one of: `function` (a Python `module:function`, called
in-process), `tool` with `method` (a JSON-RPC tool), or `tool` with `command` (a files tool). A tool entry has `run`
(an argument list, never a shell string), `pin` and `timeout`. Pins belong to tools because a version is a property of
the program; a Python function is pinned by Veriphy's own version. Trust belongs to primitives, because one tool can
both search (`sage.search`) and compute (`sage.sample`).

### D2. A process only where an interpreter differs

SageMath runs in its own Python, which is often not the one running Veriphy, and takes seconds to start, so it is one
long-lived process per session. Lean is driven through the community REPL from Python functions. SHACL and `oo-horn`'s
verdict are Python functions. Only foreign tools (R, later) are commands.

### D3. JSON-RPC 2.0, one message per line

The Sage tool speaks JSON-RPC 2.0 over stdio, newline-delimited, as language servers and MCP servers do: requests
`{"jsonrpc": "2.0", "id", "method", "params"}`, responses with `result` or `error: {code, message}`. The daemon still
answers a request without `"jsonrpc"` in the old shape, so a Lean library of an earlier release keeps working.

### D4. Data never passes through a shell

`run` is an argument list. A files tool's placeholders are replaced by paths Veriphy wrote (`{input}`, `{out}`) or
files the input names (`{file:x}`); a JSON-RPC tool's values travel inside the message.

### D5. Three kinds of pin, checked before every call

`image: name@sha256:…` runs the tool in that container, which needs podman or docker. `commit` plus `sha256` fetches
and verifies a release, as `oo-horn` does. `version` compares the version the tool reports. Every output carries the
tool's name, the version found and the pin kind. A JSON-RPC tool checks its pin once, when it starts.

### D6. JSON Schema both ways

Schemas are JSON Schema (draft 2020-12), inline in `pack.yaml` or in a file of the pack. The input is checked before
anything runs and the output after it answers, so a tool that drifts is caught at the boundary.

### D7. Composites are code, their trust is computed

A composite is a function in a pack's module, registered with the primitives it calls and the one that decides. Its
class follows from its parts, never declared, so a pack cannot label a Sage-only composite `kernel`. Composites call
their parts through the same checks as any caller.

### D8. Purity is the boundary of layer 0

`veriphy.primitives` never reads `.veriphy/` or `veriphy.yaml`, and never writes a record. `assert_deterministic` runs a
primitive twice and compares the outputs, so each pack can test its own primitives.

### D9. Lean through the community REPL

`leanprover-community/repl`, pinned by commit, is built against the workspace's toolchain into the cache on first use
(about 25 seconds). One REPL runs per workspace and keeps one environment per import header. `VERIPHY_LEAN_REPL` names a
REPL binary, or `off` to run `lake env lean` per call, which gives the same output. A test checks both ways agree.

### D10. Lean is a pack, and the bridge's default is tested, not read

The `lean` pack holds the Lean primitives; the `math` pack needs `lean`. The Lean bridge keeps its default daemon
command in Lean, because reading `pack.yaml` from Lean would need Python to find Sage, and a test keeps that default
equal to the `math` pack's `sage` tool. The same test style keeps the `core` pack's `oo-horn` pin equal to the release
the checker sets up.

## Risks / Trade-offs

- [The REPL must match the toolchain] → It is built against the workspace's toolchain from a pinned commit, and the
  file fallback gives the same output when it cannot be built.
- [Version pins trust the tool's own report] → The output names the pin kind, and packs prefer image or hash pins.
- [Two request formats in the daemon for one release] → The old one is deprecated and goes in the next minor release.
