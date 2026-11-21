## MODIFIED Requirements

### Requirement: Steps command
`veriphy layers step list` SHALL list the workspace's steps with their kind and pack, and `veriphy layers step <step>` SHALL take
one argument or option per declared input. A step SHALL NOT be named `list` or `records`, and `config check` SHALL
refuse one that is.

#### Scenario: Listing
- **WHEN** `veriphy layers step list` runs with the default config
- **THEN** it lists `check` and `level` from `lean`, `meaning` from `math`, and `validate`, `reason` and `report`
  from `core`

#### Scenario: A reserved name
- **WHEN** a pack declares a step named `records`
- **THEN** `veriphy config check` names the step and says that `records` is the step group's own command
