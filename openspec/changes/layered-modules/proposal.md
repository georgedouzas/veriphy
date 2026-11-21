# Proposal

## Why

The architecture is layered, and the code should read the same way: every module belongs to one layer, a module
imports only the layers below it, and a reader finds a layer's code under the layer's name. Today the package is
organized by history: `oracle`, `sage_server`, `toolkit`, `translations`, `certificates`, `graph`, `prompts`, `steps`
and `core` sit side by side, mathematics is mixed into the core, and `steps` (layer 1) imports `graph` (layer 2).

## What Changes

- **One subpackage per layer:** `veriphy.primitives` (0), `veriphy.steps` (1), `veriphy.claims` (2),
  `veriphy.workflows` (3) and `veriphy.agents` (4), with `veriphy.core` shared below them.
- **Packs by layer:** `veriphy.packs.<name>` with a `pack.yaml` and the same layer subpackages. `core`, `lean` and
  `math` are created, and mathematics moves into `math`.
- **The moves:**

  | Today | Target |
  |---|---|
  | `veriphy.oracle`, `veriphy.sage_server` | `veriphy.packs.math.primitives.sage` |
  | `veriphy.toolkit` | `veriphy.packs.math.script`, re-exported by `veriphy.script` |
  | `veriphy.translations` | `veriphy.packs.math.primitives.translations` |
  | `veriphy.certificates` | `veriphy.packs.math.steps.certificates` |
  | `veriphy.graph` (engine, process runner, checker) | `veriphy.primitives.graph` |
  | `veriphy.graph` (the rest) | `veriphy.claims` |
  | the graph steps in `veriphy.steps` | `veriphy.claims`, registered as steps |
  | the Lean steps in `veriphy.steps` | `veriphy.packs.lean.steps`, `meaning` in `veriphy.packs.math.steps` |
  | the record store in `veriphy.core` | `veriphy.steps` |
  | `veriphy.prompts` | `veriphy.agents`, with the playbooks in `veriphy.packs.math.agents` and `veriphy.packs.core.agents` |

- **The import rule, enforced:** a test fails when a module imports a higher layer, or when a pack's layer-k code
  imports a Veriphy layer above k.
- **Steps register themselves:** the step runner keeps a registry that the packs and layers fill, so it never imports
  a higher layer. `python -m veriphy` loads every registration.
- **Deprecated aliases:** every old module path keeps working for one minor release, re-exporting the new one and
  warning once. `python -m veriphy.graph`, `python -m veriphy.prompts`, `python -m veriphy.sage_server` and the Lean
  bridge's daemon path keep working.

No behaviour changes: every test passes with only its imports updated.

Depends on `meaning-step`.

## Capabilities

### New Capabilities

- `core/module-layout`: the layer subpackages, packs by layer, the import rule, step registration and the aliases.

### Modified Capabilities

None. Behaviour is unchanged.

## Impact

- Every module under `src/veriphy/` moves, and every test's imports change.
- `pyproject.toml`: package data paths (the playbooks, the Lean assets), the `veriphy-sage-server` entry point.
- Lean: `Veriphy/Bridge.lean` starts the daemon from its new module path.
- Skills and docs: module paths in commands.
