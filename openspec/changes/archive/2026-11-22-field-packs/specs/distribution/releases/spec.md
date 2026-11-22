## MODIFIED Requirements

### Requirement: Lake consumption by tag
Each release tag SHALL be usable as a Lake dependency revision, through `[[require]] name = "veriphy"`,
`git = "https://github.com/georgedouzas/veriphy"`, `rev = "X.Y.Z"` and `subDir = "src/veriphy/packs/math/lean"`. The
Lean package (`lakefile.toml`, `lake-manifest.json`, `lean-toolchain` and its sources) SHALL live in the math pack's
`lean/` directory, and SHALL declare its mathlib revision so dependents resolve a compatible mathlib.

#### Scenario: Downstream require
- **WHEN** a fresh Lake project requires Veriphy at a release with `subDir` and runs `lake update && lake build`
- **THEN** the build succeeds and `import Veriphy` makes the `veriphy` tactic and the `#veriphy` command available

#### Scenario: Sources under lean
- **WHEN** a Lake project requires a release made after the move
- **THEN** `import Veriphy` resolves to `src/veriphy/packs/math/lean/Veriphy.lean`
