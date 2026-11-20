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
errors that name the key and its line, so a typo is never silently ignored. `pack.yaml` uses the same schema with
`name` and `requires` added.

### D2. Packs are data first

A pack is `pack.yaml` plus its files. Veriphy's own packs are directories inside the package, registered under the
`veriphy.packs` entry point like any third-party pack. Code a pack needs (composites, digest scopes) lives in the
pack's own module and is named from `pack.yaml` by its import path.

### D3. Order by requirement, merge by key

Packs are ordered so each comes after the packs it requires, keeping the listed order otherwise. Mappings merge
recursively, and a later scalar or list replaces an earlier one. `null` removes the key, so `tools: {sage: null}`
drops SageMath, and every primitive and step that needs it is reported unavailable.

### D4. Collisions between unrelated packs are errors

When two packs that do not require each other define the same entry, the later one does not silently win. `config
check` names both packs and the entry, and the workspace file settles it by defining the entry itself. A pack that
requires another may override its entries, since it was written knowing them.

### D5. One registry per layer

The resolved config is split into the registries of primitives (tools, primitives), steps (steps, scopes), claims
(levels, conventions), workflows and playbooks. A layer receives its registry as a parameter, so it reads no config
of a layer above it, and each layer's module registers its own checks with `config check`.

### D6. The digest covers meaning, not formatting

The config digest is the digest of the resolved config as canonical JSON, so a comment or a reordering in
`veriphy.yaml` does not invalidate records, and a changed pin does.

## Risks / Trade-offs

- [YAML adds a dependency] → PyYAML is small and already in most environments. The schema check reuses `jsonschema`
  from `primitives`.
- [Requiring the workspace to settle collisions adds friction] → It happens only for unrelated packs defining the same
  name, which is exactly the case that would otherwise go wrong unnoticed.
