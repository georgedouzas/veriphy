## MODIFIED Requirements

### Requirement: Packs
An entry of `packs` SHALL be a name, of a shipped pack or one resolved through the `veriphy.packs` entry point, or a
path to a directory holding a `pack.yaml` in the workspace file's schema with `name` and `requires` added. The
framework pack SHALL come first in every workspace, unnamed, and each other pack SHALL be loaded after the packs it
requires. A local pack's Python SHALL import from its directory, and a tool's command MAY name `{pack}`, the pack's
directory.

#### Scenario: Requirements are loaded
- **WHEN** a workspace has no `veriphy.yaml`
- **THEN** the resolved config holds the framework pack and `math`, in that order

#### Scenario: A field without Lean
- **WHEN** a workspace lists `packs: [./packs/economics]`, whose function sits beside its `pack.yaml`
- **THEN** the resolved config holds that pack's entries, its function imports, and no Lean or SageMath primitive
