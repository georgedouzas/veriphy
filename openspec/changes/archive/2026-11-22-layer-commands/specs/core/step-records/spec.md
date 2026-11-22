## MODIFIED Requirements

### Requirement: Step command
`veriphy layers step <step> [arguments]` SHALL run a step and print the record's path and status, or the record itself with
`--json`. It SHALL exit with status 0 on an accepting status, 1 on a refusal or counterexample, 2 on bad usage and 3
on an unchecked result. `veriphy layers step records` SHALL list records and show one by digest.

#### Scenario: Machine-readable result
- **WHEN** an agent runs `veriphy layers step levels MyProject --json`
- **THEN** it reads the full record from standard output, with no other text
