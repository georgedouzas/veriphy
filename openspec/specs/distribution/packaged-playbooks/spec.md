# distribution/packaged-playbooks Specification

## Purpose
Ships the playbooks, recipes, templates and recipe assets inside the `veriphy` Python package, at the version of the toolkit they describe, and gives agents access to them through `python -m veriphy.prompts`, so no clone of the repository is needed.

## Requirements

### Requirement: Playbooks ship in the Python package
The `veriphy` Python package SHALL contain the playbooks, the recipes, their templates and the recipe assets, at the
same version as the toolkit. Each file SHALL have one source in the repository.

#### Scenario: Installed from the wheel
- **WHEN** a user runs `sage -pip install veriphy` on a machine with no clone of the repository
- **THEN** the installed package contains `prove.md`, every recipe, every template and every recipe asset

### Requirement: Prompts command
`python -m veriphy.prompts` SHALL provide `path` (the directory holding the content), `list` (every playbook, recipe,
template and asset), `show <name>` (one file, by its relative name with the extension optional) and `copy <name>` (a
template into `.veriphy/certificates/`, or an asset into `.veriphy/lean/VeriphyAssets/`, of the current workspace).
An unknown name SHALL exit with status 1 and name the closest matches.

#### Scenario: Showing a recipe
- **WHEN** an agent runs `sage -python -m veriphy.prompts show recipes/sos`
- **THEN** the command prints the SOS recipe

#### Scenario: Copying a template
- **WHEN** an agent runs `copy recipes/templates/farkas` in a workspace without `.veriphy/certificates/farkas.sage`
- **THEN** the command writes that file and prints its path

#### Scenario: No overwrite
- **WHEN** the destination file already exists
- **THEN** the command exits with status 1, names the file and leaves it unchanged

### Requirement: Skills read the installed package
The `prove`, `certify` and `research` skills SHALL locate their playbooks with `python -m veriphy.prompts path`, and
SHALL NOT read `VERIPHY_HOME` or require a clone of the repository. The plugin copy and the repository copy of each
skill SHALL be identical.

#### Scenario: Manual install without a clone
- **WHEN** a user copies the three `SKILL.md` files into `~/.claude/skills/` and has `veriphy` installed in Sage
- **THEN** the skills find and follow the playbooks

#### Scenario: Package missing
- **WHEN** `python -m veriphy.prompts path` fails
- **THEN** the skill asks the user to run `sage -pip install veriphy` and does not proceed
