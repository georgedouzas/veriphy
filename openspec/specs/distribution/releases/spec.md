# distribution/releases Specification

## Purpose
Keeps Veriphy's three deliverables (the Lean library, the `veriphy` Python package and the Claude plugin) on one version. A release is reproducible from a tag and is published only after CI has proven it.

## Requirements

### Requirement: Versions come from the release tag
A release SHALL be a git tag `X.Y.Z` on `main`. The Python distribution's version SHALL be derived from that tag by hatch-vcs, never written in a file. The Lean library SHALL carry no version constant of its own: Lake consumers pin the tag as the dependency revision.

#### Scenario: Wheel version from the tag
- **WHEN** tag `0.4.0` is pushed and the release workflow builds the package
- **THEN** the built wheel is `veriphy-0.4.0`, and no file in the repository was edited to set that version

### Requirement: Lake consumption by tag
Each release tag SHALL be usable as a Lake dependency revision, through `[[require]] name = "veriphy"`, `git = "https://github.com/georgedouzas/veriphy"` and `rev = "X.Y.Z"`. The Lean package SHALL stay at the repository root and SHALL declare its mathlib revision so dependents resolve a compatible mathlib.

#### Scenario: Downstream require
- **WHEN** a fresh Lake project requires Veriphy at `0.4.0` and runs `lake update && lake build`
- **THEN** the build succeeds and `import Veriphy` makes the `sage_*` tactics available

### Requirement: Release gated by CI
Publishing (PyPI upload and the GitHub release) SHALL run only after every CI job passes on the tagged commit:
- the Sage-free Lean build, including the Sage-free kit tests;
- the Python checks;
- the Sage integration job, which runs the daemon unit tests and the full tactic suite with replay enabled against the package installed from the built wheel.

#### Scenario: Failing integration blocks the release
- **WHEN** the integration job fails on a tagged commit
- **THEN** nothing is uploaded to PyPI and no GitHub release is created

### Requirement: Sage-free proofs verified in CI
CI SHALL verify, on every push, that the Lean library and the kit tests build on a runner with no Sage installed.

#### Scenario: Lean job has no Sage
- **WHEN** the Lean CI job runs
- **THEN** `sage` is not available on that runner, and `lake build` and `lake build VeriphyTest.Kit` pass

### Requirement: PyPI publishing without long-lived secrets
The release workflow SHALL publish to PyPI through trusted publishing (OIDC) from the GitHub repository. It SHALL NOT use a stored API token.

#### Scenario: Publish step credentials
- **WHEN** the release workflow uploads `veriphy-X.Y.Z` to PyPI
- **THEN** it authenticates through the repository's trusted-publisher identity, and no PyPI token secret is configured

### Requirement: Template provenance
The repository SHALL record the `copier-modern-python` template source as its GitHub repository (`gh:georgedouzas/copier-modern-python`), not a local path, together with the template version and answers it was generated from. Template updates SHALL be applied with `copier update`, not by hand-copying files.

#### Scenario: Template update
- **WHEN** the template repository publishes a new tag and the author runs `copier update` from any machine
- **THEN** copier merges the template changes into the repository, and Veriphy-specific files (README, Lean sources, OpenSpec configuration) keep their local content
