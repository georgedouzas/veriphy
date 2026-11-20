# Proposal

## Why

Veriphy should serve any field that brings its own tools, and a field should not need Python to do it. Today the
tools, the levels and the recipes are fixed in code. The architecture makes one YAML file configure a workspace, with
defaults that give today's behaviour.

## What Changes

- `veriphy.yaml` at the workspace root, every key optional: `packs`, `tools`, `levels`, `steps`, `conventions`,
  `workflows`. A missing file means `packs: [math]`.
- Packs: a name is an installed Python package registered under the `veriphy.packs` entry point, a path is a directory
  with a `pack.yaml` in the same schema. Veriphy ships `core` (Lean, the claim graph, `oo-horn`) and `math` (`core`
  plus SageMath, the recipes and today's levels).
- The merge: core defaults, then each pack in order, then the workspace file. A later value wins key by key, and `null`
  removes an entry.
- Trust classes and levels: six classes (`kernel`, `checker`, `reproduction`, `oracle`, `measurement`, `search`), and
  levels declared with their class and the level they sit above. **BREAKING** for nobody in practice: the five levels
  move from code into the `math` pack, with the same names and order.
- `python -m veriphy config show` prints the resolved config with the source of each value, and `config check`
  enforces the rules. The config digest enters every step record.

Depends on `step-records`.

## Capabilities

### New Capabilities

- `core/workspace-config`: the file, the schema, packs, the merge, trust classes, levels and the two commands.

### Modified Capabilities

- `research/claim-graph`: the vocabulary's levels come from the resolved config.
- `certificates/test-fallback`: each level names its trust class.

## Impact

- New: `veriphy.core` config (schema, merge, check), `veriphy/packs/core/pack.yaml`, `veriphy/packs/math/pack.yaml`.
- `veriphy.graph`: the level individuals and their order are generated from the config.
- `pyproject.toml`: the `veriphy.packs` entry points.
