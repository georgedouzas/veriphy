# Design

## Context

The Sage daemon speaks JSON lines and is started by the Lean bridge from `VERIPHY_SAGE_CMD`, `VERIPHY_SAGE_SERVER`
and `VERIPHY_SAGE_TIMEOUT`. `_checker.py` pins `oo-horn` by commit and SHA-256 and sets it up on first use. The steps
of `step-records` and `meaning-step` run `lake env lean --json` on a generated file, so each Lean step loads Mathlib
again, which costs minutes. The daemon methods are listed in `METHODS`, each a Python function with keyword arguments
and no declared schema.

## Goals / Non-Goals

**Goals:**

- Every operation Veriphy relies on is a primitive with a schema, a trust class and a pin, callable by hand.
- Lean, SageMath and `oo-horn` sit behind the same interface, and users see no change in behaviour.
- A Lean primitive costs Mathlib's load once per session, not once per call.

**Non-Goals:**

- Selecting packs per workspace and the `veriphy.yaml` file (`packs-and-config`).
- Declaring steps in YAML (`declarative-steps`). Steps keep their Python definitions and call primitives.
- Levels and the grant rule (`claims-and-trust`). Primitives declare a trust class, and nothing enforces it yet.
- Running tools in containers. An image pin is checked when a container runtime exists, and the reproduction pack is
  its first user.

## Decisions

### D1. A tool is a process, a primitive is an operation

A tool entry has `contract`, `run` (an argument list, never a shell string), `pin` and `timeout`. A primitive entry has
`tool`, `method` (json-lines) or `command` placeholders (files), `trust`, `input`, `output` and `seed`. Pins belong to
tools because a version is a property of the process. Trust belongs to primitives because one tool can both search
(`sage.search`) and compute (`sage.sample`).

### D2. Data never passes through a shell

`run` is an argument list. Placeholders are replaced by paths Veriphy wrote, or, for json-lines, values travel inside
the JSON request. So an input value cannot inject a command, whatever it contains.

### D3. Three kinds of pin, checked before every call

`image: name@sha256:…` runs the tool in that container. `commit` with `sha256` fetches and verifies a release, as
`oo-horn` does today. `version` runs the installed tool and compares its reported version. Every output carries the
tool's name, the version found and the pin kind, so a record can say how strong its pin was. A json-lines tool checks
its pin once, when the process starts.

### D4. JSON Schema both ways

Schemas are JSON Schema (draft 2020-12) files in the pack. The input is checked before the tool starts and the output
after it answers, so a tool that drifts is caught at the boundary. The daemon methods get schemas written from their
current signatures, and a test checks that every method in `METHODS` has one.

### D5. Composites are code, their trust is declared

A composite is a function in a pack's module, registered with the primitives it calls and the one that decides. Its
class is computed by that rule, not declared, so a pack cannot label a Sage-only composite `kernel`. Composites
call primitives through the same checks as any caller.

### D6. Purity is the boundary of layer 0

`veriphy.primitives` never reads `.veriphy/` or `veriphy.yaml`, and never writes a record. The registry is built from
the installed packs and passed in. A primitive that uses randomness must declare `seed`, and a test helper,
`assert_deterministic`, runs a primitive twice and compares the outputs, so each pack can test its own primitives.

### D7. The Lean session wraps the community REPL

The `lean` tool runs `leanprover-community/repl`, pinned to the commit matching the workspace's toolchain, under
`lake env`. It keeps one environment per import header: a request whose header matches an open environment reuses it,
and another header starts a new one. `lean.check`, `lean.serialize` and `lean.level` send commands to that
environment. Building our own server on Lean's frontend stays possible behind the same tool entry.

### D8. Lean is a pack

The `lean` pack holds the Lean tool and primitives, and points at the Lean library in `lean/` for its assets. The
`math` pack needs `lean`, because `veriphy certify`, `#veriphy test` and `certify` emit Lean proofs. The `core` pack does not
need Lean: `oo-horn` is a pinned binary, built with Lean only when no prebuilt release fits the platform.

## Risks / Trade-offs

- [The REPL must match the toolchain] → It is pinned by commit per toolchain, and `primitive describe lean.check`
  names both. A missing or mismatched REPL falls back to one `lake env lean` process per call, which is slower but
  gives the same output.
- [Version pins trust the tool's own report] → The output names the pin kind, and packs prefer image or hash pins.
- [A schema per daemon method is a large first step] → The schemas are written once from the signatures, and the test
  of D4 keeps them complete.
