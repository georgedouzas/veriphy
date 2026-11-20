# Spec Delta

## MODIFIED Requirements

### Requirement: Agent-agnostic and progressively loaded
Recipes SHALL be plain markdown readable by any agent, shipped in the Python package, indexed from the `prove`
playbook, and loaded one at a time rather than all at once. A dedicated `certify` skill SHALL guide the build loop:
inspect `problem`, choose a recipe, adapt its template, run, read the combined feedback, iterate.

#### Scenario: Agent picks a recipe
- **WHEN** the agent faces an inequality with hypotheses
- **THEN** the playbook's index leads it to the Farkas or hint-search recipe by the stated decision rule, without loading the other recipes

#### Scenario: Recipe from the installed package
- **WHEN** an agent with no clone of the repository needs the Farkas recipe
- **THEN** it reads it from the installed package, at the version of the installed toolkit
