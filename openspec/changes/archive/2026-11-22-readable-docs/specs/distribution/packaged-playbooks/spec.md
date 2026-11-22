## ADDED Requirements

### Requirement: Playbooks by pack

`agents list` and `agents show` SHALL take `--pack`, `math` by default, as `agents path` does, and SHALL read only
that pack's files.

#### Scenario: The statistics playbooks

- **WHEN** `veriphy layers agents list --pack statistics` runs
- **THEN** it lists `reproduce.md` and `skills/reproduce/SKILL.md`, and no math recipe
