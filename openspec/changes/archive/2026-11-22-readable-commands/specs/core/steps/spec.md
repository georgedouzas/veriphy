## MODIFIED Requirements

### Requirement: Comparison
A step MAY declare `compare` with an output `field`, an input `against` and a `tolerance`, a number or `reported`, half
a unit in the last digit the claim reports. Its status SHALL then be `agrees` when the two values differ by at most the
tolerance and `differs` otherwise, with both values recorded, and it SHALL grant its level only when the comparison ran
and agreed.

#### Scenario: Within tolerance
- **WHEN** the output's `estimate` is 0.4213 and the claimed value 0.4210, with tolerance 0.001
- **THEN** the status is `agrees`, and the record holds both values

#### Scenario: A rounded figure
- **WHEN** the estimate is 0.1265 and the claim reports 0.127, with `tolerance: reported`
- **THEN** the status is `agrees` within 0.0005, and the record holds both values

#### Scenario: No claimed value
- **WHEN** a step that compares runs without the input it compares against
- **THEN** it records the tool's status and grants no level

## ADDED Requirements

### Requirement: Accepted statuses
A step MAY name the statuses that mean success with `accepts`. Any other status SHALL then be recorded as `refused`,
with the tool's word kept as `result`. `config check` SHALL refuse a step that grants a level over a primitive whose
statuses include words Veriphy doesn't know when the step names no `accepts`, and SHALL refuse any unknown field of a
step or of an input.

#### Scenario: A tool's own words
- **WHEN** a step with `accepts: [found]` runs a tool that answers `missing`
- **THEN** the record's status is `refused`, its `result` is `missing`, and no level is granted
