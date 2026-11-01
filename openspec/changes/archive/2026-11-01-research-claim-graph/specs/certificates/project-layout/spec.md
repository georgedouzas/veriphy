# Spec Delta

## MODIFIED Requirements

### Requirement: One root for Veriphy artifacts
Every Veriphy artifact in a downstream project SHALL live under `.veriphy/` at the root of the Lean workspace. Veriphy SHALL NOT create or read Veriphy artifacts anywhere else in the project. The layout is:
- `.veriphy/certificates/`: certificate scripts (`.sage`);
- `.veriphy/translations/`: project translation and rewrite entries (`.json`);
- `.veriphy/lean/`: Lean sources copied from Veriphy (recipe assets, the bundled `VeriphyCheck` file);
- `.veriphy/coverage/`: coverage reports;
- `.veriphy/tests/`: test records written by `sage_test`;
- `.veriphy/graph/`: the research claim graph, with `sources/` (Turtle files per source and provenance), `lean/` (the
  Lean export) and `runs/` (reasoning certificates).

#### Scenario: Fresh project
- **WHEN** an agent saves its first script and its first translation entry in a project with no `.veriphy/`
- **THEN** `.veriphy/certificates/` and `.veriphy/translations/` are created, and nothing else in the project changes

#### Scenario: Removing Veriphy
- **WHEN** a user deletes `.veriphy/` from a project whose proofs use only emitted replacements and no copied assets
- **THEN** the project still builds

#### Scenario: First graph
- **WHEN** an agent extracts the first source of a project into the graph
- **THEN** `.veriphy/graph/sources/` is created with the source's file, and nothing outside `.veriphy/` changes
