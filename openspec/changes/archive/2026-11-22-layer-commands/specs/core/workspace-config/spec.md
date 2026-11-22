## ADDED Requirements

### Requirement: Pack commands
A pack MAY declare programs in a `commands` section, each as `{command: <module>:<attribute>, help: <one line>}`
naming a click command. `veriphy pack <pack>` SHALL group a selected pack's programs, importing each only when it is
named, and `veriphy pack list` SHALL list the selected packs, each after the packs it requires.

#### Scenario: The math pack's programs
- **WHEN** a user runs `veriphy pack math --help` with the default config
- **THEN** it lists `certificates` and `translations` with their help, and `veriphy pack math certificates list` lists
  the saved scripts

#### Scenario: An unselected pack
- **WHEN** a workspace lists `packs: [core]`
- **THEN** `veriphy pack --help` lists `list` and no `math` group
