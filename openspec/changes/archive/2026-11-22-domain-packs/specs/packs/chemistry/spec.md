## ADDED Requirements

### Requirement: Chemistry pack
Veriphy SHALL ship a `chemistry` pack whose steps `check-molecule` and `check-reaction` use RDKit to check a molecule's
formula and molar mass from its SMILES, and that a reaction balances element by element, hydrogens included, granting
`structure-checked` (checker), with the convention `standard-state`.

#### Scenario: An unbalanced reaction
- **WHEN** `check-reaction "[H][H] + O=O >> O"` runs
- **THEN** it is refused, naming oxygen's counts on each side
