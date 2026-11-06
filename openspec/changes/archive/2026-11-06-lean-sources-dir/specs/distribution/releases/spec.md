# Spec Delta

## MODIFIED Requirements

### Requirement: Lake consumption by tag
Each release tag SHALL be usable as a Lake dependency revision, through `[[require]] name = "veriphy"`, `git = "https://github.com/georgedouzas/veriphy"` and `rev = "X.Y.Z"`, with no other key. The Lean package configuration (`lakefile.toml`, `lake-manifest.json`, `lean-toolchain`) SHALL stay at the repository root, its sources SHALL live under `lean/`, and it SHALL declare its mathlib revision so dependents resolve a compatible mathlib.

#### Scenario: Downstream require
- **WHEN** a fresh Lake project requires Veriphy at `0.4.0` and runs `lake update && lake build`
- **THEN** the build succeeds and `import Veriphy` makes the `sage_*` tactics available

#### Scenario: Sources under lean
- **WHEN** a Lake project requires a release made after the sources moved, with the same three keys as before
- **THEN** `lake update && lake build` succeeds without `subDir`, and `import Veriphy` resolves to `lean/Veriphy.lean`
