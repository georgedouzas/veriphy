# Design

## Context

The levels are fixed in `vocabulary.ttl` and `_vocabulary.LEVELS`, and in Lean's `levelOf`. Tools are found through
environment variables (`VERIPHY_SAGE_CMD`, `VERIPHY_OO_HORN`). The Physlib translation pack is the one existing plug-in
mechanism, in Lean. The record format of `step-records` has a config digest that is a placeholder until this change.

## Goals / Non-Goals

**Goals:**

- One file describes a workspace, and no file means today's behaviour.
- A config that would break determinism or trust is refused before any step runs.

**Non-Goals:**

- The tool contracts and pinning enforcement at run time (`tool-contracts`), beyond the schema.
- Workflows as data (`workflows-as-data`), beyond accepting the key.

## Decisions

### D1. A JSON Schema, versioned

`veriphy.yaml` has `version: 1` and is validated against a JSON Schema shipped with the package. Unknown keys are
errors, so a typo is never silently ignored.

### D2. Packs are data

A pack is `pack.yaml` plus its files. Veriphy's `core` and `math` packs are directories inside the package, registered
as entry points like any third-party pack. Pack code, when a pack needs any, lives in the pack's own Python package.

### D3. Merge by key, `null` removes

Mappings merge recursively and a later scalar or list replaces an earlier one. `null` removes the key, so
`tools: {sage: null}` drops SageMath and every step that needs it is reported unavailable.

### D4. One order of levels

Each level names its trust class and the level directly below it (`above`). `config check` requires that the levels
form one chain from `none`, so effective levels stay a minimum over one order across fields.

### D5. Trust classes are fixed

The six classes are part of the schema, not configurable. A pack can add levels and tools, but cannot invent a class
that grants proof-like trust.

### D6. Lean reads levels from Lean

`#veriphy_levels` keeps computing the five Lean levels from the proof term. The config declares them with class
`kernel` (and `oracle-test` with `oracle`), and the graph takes their order from the config. A pack's other levels come
only from step records.

## Risks / Trade-offs

- [YAML adds a dependency] → PyYAML is small and already in most environments. The schema check uses `jsonschema`.
- [Two sources of level names, Lean and the config] → `config check` fails when the `math` pack and Lean disagree, and
  a test keeps them equal.
