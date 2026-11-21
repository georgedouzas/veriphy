# Design

## Context

After `primitives`, packs are directories with a `pack.yaml` holding `tools` and `primitives`, and the registry loads
every installed pack. The record format of `step-records` has a config digest that is a placeholder. The Physlib
translation pack is the one plug-in mechanism outside Python, in Lean.

## Goals / Non-Goals

**Goals:**

- One file describes a workspace, and no file means today's behaviour.
- A pack can extend every layer, and a workspace can override any entry of any pack.
- A config that would break determinism or trust is refused before anything runs.

**Non-Goals:**

- The meaning of the step, level and workflow entries. This change accepts and merges them by their schema, and the
  changes that build those layers (`declarative-steps`, `claims-and-trust`, `workflows-as-data`) add their checks.

## Decisions

### D1. A JSON Schema, versioned

`veriphy.yaml` has `version: 1` and is validated against a JSON Schema shipped with the package. Unknown keys are
errors that name the key and its path, as JSON Schema reports them, so a typo is never silently ignored. `pack.yaml` uses the same schema with
`name` and `requires` added.

### D2. Packs are data first

A pack is `pack.yaml` plus its files. Veriphy's own packs are directories inside the package, registered under the
`veriphy.packs` entry point like any third-party pack. Code a pack needs (composites, digest scopes) lives in the
pack's own module and is named from `pack.yaml` by its import path.

### D3. Order by requirement, merge by JSON Merge Patch

Packs are ordered so each comes after the packs it requires, keeping the listed order otherwise. Each pack, then the
workspace file, is applied as a JSON Merge Patch (RFC 7396): mappings merge recursively, a later value replaces an
earlier one, and `null` removes the key. So `tools: {sage: null}` drops SageMath, and every primitive and step that
needs it is reported unavailable. The standard says what the merge does; Veriphy adds nothing to it.

### D4. Collisions between unrelated packs are errors

When two packs that do not require each other define the same entry, the later one does not silently win. `config
check` names both packs and the entry, and the workspace file settles it by defining the entry itself. A pack that
requires another may override its entries, since it was written knowing them.

### D5. One mapping, one section per layer

The resolved config is one mapping. Each layer reads its own sections (primitives: `tools`, `primitives`; steps:
`steps`, `scopes`; claims: `levels`, `conventions`; workflows; playbooks), and receives them as a parameter, so it
reads nothing of a layer above it. `config check` is the JSON Schema and the checks across sections (a primitive
names a declared tool), in one place.

### D6. The digest covers meaning, not formatting

The config digest is the digest of the resolved config as canonical JSON, so a comment or a reordering in
`veriphy.yaml` does not invalidate records, and a changed pin does.

## Risks / Trade-offs

- [YAML adds a dependency] → PyYAML came with `primitives`, as did `jsonschema`.
- [Requiring the workspace to settle collisions adds friction] → It happens only for unrelated packs defining the same
  name, which is exactly the case that would otherwise go wrong unnoticed.
