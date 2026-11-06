# Proposal

## Why

The Lean side of the repository is spread over eleven entries at the root: three root modules (`Veriphy.lean`,
`VeriphyCheck.lean`, `VeriphyTest.lean`), their three directories, `assets/`, the `coverage/` Lake project and the three
Lake configuration files. They sit beside the Python package, the playbooks and the docs, so the root does not show
what the repository is made of. The Python side is already contained in `src/` and `tests/`.

## What Changes

- The Lean sources move under `lean/`: the three root modules and their directories, `assets/VeriphyAssets/` and the
  `coverage/` Lake project.
- `lakefile.toml`, `lake-manifest.json` and `lean-toolchain` stay at the repository root, and a package-level
  `srcDir = "lean"` points Lake at the sources. Users' `[[require]]`, module names, `import Veriphy`, the mathlib cache,
  `.lake/` and the workspace root are unchanged.
- Every path that names a moved file is updated: the coverage lakefile, `scripts/bundle_check.py`,
  `scripts/sync_tables.sh`, docstrings, the developer docs, the user guide, recipes (asset paths) and the constitution.
- A spec that names a Lean file by path names its module instead, so it survives later moves.
- The stray untracked `https:` directory at the root, left by a clone given a URL as its path, is deleted.

No user-facing behaviour changes, and the change does not need a release of its own.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `distribution/releases`: the Lake package configuration stays at the root and its sources live under `lean/`, with
  the dependency declaration users write unchanged.
- `certificates/linear-algebra-certificates`: the packaging lemmas are named by module, not by file path.

## Impact

- Lean: `lakefile.toml` (`srcDir`), `lean/coverage/lakefile.toml` (`path = "../.."`). No `.lean` file changes content.
- Python and scripts: `scripts/bundle_check.py`, `scripts/sync_tables.sh`, a docstring in `veriphy.toolkit._linear`.
- Documents: `docs/development/index.md`, `docs/development/benchmark.md`, `docs/development/coverage.md`,
  `docs/overview/user_guide.md`, recipes under `prompts/recipes/`, `openspec/constitution.md`.
- CI needs no path change, because it builds Lake targets from the root.
