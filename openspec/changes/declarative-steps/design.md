# Design

## Context

`step-records` defined `Step(name, kind, prepare, run)` with a Python `prepare` that reads the inputs and a Python
`run` that calls the tool. `lean_sources` hashes every `.lean` file of the workspace outside hidden directories, plus
`lean-toolchain` and `lake-manifest.json`. After `primitives`, every tool call is a primitive, and after
`packs-and-config`, the steps registry exists but holds nothing.

## Goals / Non-Goals

**Goals:**

- A field adds a step with YAML alone, as long as its primitive exists.
- A Lean record stays valid while unrelated files change.

**Non-Goals:**

- Levels and the grant rule (`claims-and-trust`). A step declares the levels it may grant, and this change checks only
  that they are named.
- Sequencing steps (`workflows-as-data`).

## Decisions

### D1. A step is a primitive with declared inputs

```yaml
steps:
  check:
    kind: check
    primitive: lean.check
    inputs:
      file: {scope: lean-imports}
    status: {from: status}
    grants: []
```

An input with no scope has the scope `value`. The runner digests each input through its scope, calls the primitive with
the inputs as its JSON input, and records the output. `status.from` names the output field holding the status, and a
`map` can rename values. Python steps survive only as composites and scopes, in the packs.

### D2. Scopes are named functions

A scope maps an input value to the content its digest covers. `value`, `file` and `files` are built in. A pack names a
scope in `pack.yaml` with the import path of a function that takes the workspace root and the value and returns the
content. `lean-imports` follows `import` lines inside the workspace, with the toolchain and the manifest standing for
everything outside it.

### D3. Comparison is generic

`compare: {field, against, tolerance}` reads `field` from the output and the input named by `against`, and sets the
status to `agrees` or `differs`, recording both values. It serves the reproduction pack and any numerical claim, and
needs no pack code.

### D4. Agent steps record artifacts

An agent step declares one input, its artifact, and `veriphy <step> <artifact> --by <name>` records the
artifact's digest and author with status `written`. Running nothing, it is still a record, so workflows can see that
the artifact exists and which version later steps used.

### D5. The command follows the declaration

Each input becomes a positional argument when it is required and an option otherwise, with its scope in the help. The
`--seed`, `--rerun` and `--json` options and the exit statuses stay as in `step-records`.

## Risks / Trade-offs

- [`lean-imports` misses a dependency] → It follows imports, and the toolchain and manifest digests cover everything
  outside the workspace. A test edits an imported file and expects a new digest.
- [Narrower digests change existing records' digests once] → Old records stay readable, and the change log says that
  Lean steps run once more after upgrading.
