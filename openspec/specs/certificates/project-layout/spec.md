# certificates/project-layout Specification

## Purpose
Keeps everything Veriphy creates or reads in a downstream project under one directory, `.veriphy/` at the project root, so its artifacts are easy to find, review, commit and remove.

## Requirements

### Requirement: One root for Veriphy artifacts
Every Veriphy artifact in a downstream project SHALL live under `.veriphy/` at the root of the Lean workspace. Veriphy SHALL NOT create or read Veriphy artifacts anywhere else in the project. The layout is:
- `.veriphy/certificates/`: certificate scripts (`.sage`);
- `.veriphy/translations/`: project translation and rewrite entries (`.json`);
- `.veriphy/lean/`: Lean sources copied from Veriphy (recipe assets, the bundled `VeriphyCheck` file);
- `.veriphy/coverage/`: coverage reports.

#### Scenario: Fresh project
- **WHEN** an agent saves its first script and its first translation entry in a project with no `.veriphy/`
- **THEN** `.veriphy/certificates/` and `.veriphy/translations/` are created, and nothing else in the project changes

#### Scenario: Removing Veriphy
- **WHEN** a user deletes `.veriphy/` from a project whose proofs use only emitted replacements and no copied assets
- **THEN** the project still builds

### Requirement: Proofs stay project code
The project's own Lean sources and committed proofs SHALL stay where the project keeps them. Emitted replacements are project code, not Veriphy artifacts, and Veriphy SHALL never move them into `.veriphy/`.

#### Scenario: Committing a replacement
- **WHEN** an agent replaces a `sage_run` call in `Project/Physics/Anomaly.lean`
- **THEN** the replacement stays in that file, and only the script goes into `.veriphy/certificates/`

### Requirement: Root resolution
Veriphy SHALL resolve `.veriphy/` against the Lean workspace root: the directory holding the root `lakefile.toml` or `lakefile.lean`. Commands run from a subdirectory SHALL find the same `.veriphy/`. The Python catalogs SHALL search upward from the working directory for the workspace root, and SHALL accept an explicit `--root`.

#### Scenario: Running from a subdirectory
- **WHEN** `sage -python -m veriphy.certificates list` runs in `Project/Sub/Dir`
- **THEN** it lists `Project/.veriphy/certificates/`

### Requirement: Copied Lean sources build as a library
Lean files copied into `.veriphy/lean/` SHALL build through a `lean_lib` the project declares with `srcDir := ".veriphy/lean"`. The recipes that copy an asset SHALL give the exact `lakefile` stanza, and the copied files SHALL import mathlib only.

#### Scenario: Copying the coordinate-geometry asset
- **WHEN** a project copies `CoordinateGeometry.lean` into `.veriphy/lean/` and adds the stanza
- **THEN** its own files can `import CoordinateGeometry`, and `lake build` succeeds

### Requirement: Migration from the 0.1.0 layout
When a project has a top-level `certificates/` directory of scripts (the 0.1.0 layout) and no `.veriphy/certificates/`, the catalog SHALL still list those scripts, warn that the layout moved, and print the `git mv` command that moves them. `sage_run file` SHALL keep running scripts by any explicit relative path.

#### Scenario: Old layout
- **WHEN** `veriphy.certificates list` runs in a project with `certificates/anomaly.sage` and no `.veriphy/`
- **THEN** it lists `anomaly`, warns that scripts belong in `.veriphy/certificates/`, and prints `git mv certificates .veriphy/certificates`
