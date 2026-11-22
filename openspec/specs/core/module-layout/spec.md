# core/module-layout Specification

## Purpose
Organize the package by layer, so a module's path names its layer and its imports respect the layers: primitives, steps, claims, workflows and agents over the shared core, with each pack holding the layer subpackages it needs.

## Requirements

### Requirement: One subpackage per layer
The package SHALL hold `veriphy.primitives` (layer 0), `veriphy.steps` (1), `veriphy.claims` (2), `veriphy.workflows`
(3) and `veriphy.agents` (4), with `veriphy.core` shared below them and the facades `veriphy` and `veriphy.script`
above them. Each pack SHALL be `veriphy.packs.<name>` with a `pack.yaml` and only the layer subpackages it needs.

#### Scenario: Mathematics is a pack
- **WHEN** a reader looks for the Sage session, the script helpers and the translation tables
- **THEN** they are under `veriphy.packs.math`, and no module outside `veriphy.packs.math` imports SageMath

### Requirement: Import rule
A module of layer k SHALL import only `veriphy.core` and modules of layers below k, and a pack's module in its
layer-k subpackage SHALL import only Veriphy's layers up to k. A test SHALL enforce the rule.

#### Scenario: An upward import
- **WHEN** a module in `veriphy.steps` imports `veriphy.claims`
- **THEN** the layer test fails, naming the module, the import and both layers

### Requirement: Step registration
`veriphy.steps` SHALL keep a registry of steps that layers and packs fill when imported, and the step command SHALL
load every registration before it runs.

#### Scenario: A step from a higher layer
- **WHEN** `python -m veriphy layers step appendix` runs
- **THEN** the `report` step registered by `veriphy.claims` runs, and `veriphy.steps` imports no higher layer

### Requirement: Behaviour unchanged
Every command, Sage method, Lean tactic and step SHALL behave as before this change.

#### Scenario: The suite
- **WHEN** the test suite runs with only its imports updated
- **THEN** every test passes, and the Lean test suite builds

### Requirement: No old module paths
The package SHALL contain only the layer modules, the packs and the facades `veriphy`, `veriphy.script` and
`veriphy.__main__`.

#### Scenario: An old import
- **WHEN** a script runs `from veriphy.toolkit import Lean`
- **THEN** it fails with `ModuleNotFoundError`, and `from veriphy.script import Lean` works
