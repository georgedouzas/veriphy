# Proposal

## Why

Configuration is shared by every layer, and it is how a field extends Veriphy without Python. After `primitives`,
every installed pack is always active, and nothing else is configurable. A workspace should be able to choose its
packs, add its own, and override any entry, with defaults that give today's behaviour.

## What Changes

- `veriphy.yaml` at the workspace root, every key optional: `version`, `packs`, `tools`, `primitives`, `scopes`,
  `steps`, `levels`, `conventions`, `workflows` and `playbooks`. A missing file means `packs: [math]`.
- `pack.yaml` uses the same schema, plus `name` and `requires`. A pack in `packs` is a name (an installed pack, through
  the `veriphy.packs` entry point) or a path to a directory.
- The merge: each pack after the packs it requires, then the workspace file, applied as JSON Merge Patches (RFC
  7396). Two packs that do not require each other and define the same entry are an error that names both, and the
  workspace file decides.
- One resolved mapping, of which each layer reads its own sections.
- `veriphy config show` prints the resolved config with the source of each value, and `config check`
  validates it. The digest of the resolved config enters every step record.
- The `primitive` command and the steps see only the selected packs' primitives.

Depends on `primitives`.

## Capabilities

### New Capabilities

- `core/workspace-config`: the two files, packs and their requirements, the merge, collisions, the sections per
  layer, the two commands and the config digest.

### Modified Capabilities

None.

## Impact

- New: `veriphy.core.config` (schema, loading, merge, commands).
- `veriphy.primitives`: its registry is built from the resolved config's sections instead of every installed pack.
- `veriphy.core`: the config digest in step records, a placeholder until now.
