## MODIFIED Requirements

### Requirement: Root resolution
Veriphy SHALL resolve `.veriphy/` against the workspace root: the nearest directory, from the working directory
upwards, holding `veriphy.yaml`, `lakefile.toml` or `lakefile.lean`. Commands run from a subdirectory SHALL find the
same `.veriphy/`, and every command SHALL accept an explicit `--root`.

#### Scenario: Running from a subdirectory
- **WHEN** `veriphy pack math certificates list` runs in `Project/Sub/Dir`
- **THEN** it lists `Project/.veriphy/certificates/`

#### Scenario: A workspace without Lean inside a Lean workspace
- **WHEN** `Project/analysis/veriphy.yaml` selects `packs: [reproduction]` and a command runs in `Project/analysis`
- **THEN** the workspace root is `Project/analysis`, and its packs are `core` and `reproduction`
