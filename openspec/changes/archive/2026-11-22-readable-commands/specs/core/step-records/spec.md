## MODIFIED Requirements

### Requirement: Step command
`veriphy layers step <step> [arguments]` SHALL run a step and print, in plain words, what it ran on and its result,
the details that explain the result (an error, the compared values, a counterexample, what breaks, who wrote an
artifact), the level it granted with its trust class, and the record's path, saying when the record was replayed. With
`--json` it SHALL print the record and nothing else. It SHALL exit with status 0 on an accepting status, 1 on a refusal
or counterexample, 2 on bad usage and 3 on an unchecked result, and `veriphy layers step records` SHALL list records and
show one by digest.

#### Scenario: A comparison
- **WHEN** `veriphy layers step reproduce analysis.py survey.csv --claimed 0.127` reproduces 0.1265
- **THEN** it prints `reproduce analysis.py: agrees`, the found and claimed values with the tolerance, the level
  `reproduced (reproduction)` and the record's path

#### Scenario: Machine-readable result
- **WHEN** an agent runs `veriphy layers step levels MyProject --json`
- **THEN** it reads the full record from standard output, with no other text
