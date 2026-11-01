# certificates/project-layout Specification

## Purpose
Keeps everything Veriphy creates or reads in a downstream project under one directory, `.veriphy/` at the project root, so its artifacts are easy to find, review, commit and remove.

## Requirements

### Requirement: One root for Veriphy artifacts
Every Veriphy artifact in a downstream project SHALL live under `.veriphy/` at the root of the Lean workspace. Veriphy SHALL NOT create or read Veriphy artifacts anywhere else in the project.

#### Scenario: Fresh project
- **WHEN** an agent saves its first script and its first translation entry in a project with no `.veriphy/`
- **THEN** `.veriphy/certificates/` and `.veriphy/translations/` are created, and nothing else in the project changes

#### Scenario: Removing Veriphy
- **WHEN** a user deletes `.veriphy/` from a project whose proofs use only emitted replacements and no copied assets
- **THEN** the project still builds

#### Scenario: First graph
- **WHEN** an agent extracts the first source of a project into the graph
- **THEN** `.veriphy/graph/sources/` is created with the source's file, and nothing outside `.veriphy/` changes

### Requirement: Directories under the project root
The directories under `.veriphy/` SHALL be `certificates/` (certificate scripts), `translations/` (translation and rewrite entries), `lean/` (Lean sources copied from Veriphy), `coverage/` (coverage reports), `tests/` (test records of `sage_test`) and `graph/` (the research claim graph).

#### Scenario: Locating an artifact
- **WHEN** a user looks for the certificate of a reasoning run of the research graph
- **THEN** it is under `.veriphy/graph/runs/`, and a test record is under `.veriphy/tests/`

#### Scenario: The graph directory
- **WHEN** a project has a research claim graph
- **THEN** `.veriphy/graph/` holds `sources/` (Turtle files per source and provenance), `lean/` (the Lean export) and `runs/` (reasoning certificates)

#### Scenario: Copied Lean sources and scripts
- **WHEN** an agent copies a recipe asset and saves a certificate script
- **THEN** the asset is under `.veriphy/lean/` and the script, a `.sage` file, is under `.veriphy/certificates/`

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
