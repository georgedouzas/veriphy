# core/steps Specification

## Purpose
Declare a step as a primitive with inputs, each digested by its scope, a status field, a comparison and the level it grants, so that a pack adds steps in YAML alone and each step's command, record and replay follow from its declaration.

## Requirements

### Requirement: Step declarations
A step SHALL be declared in the config with its `kind`, its `primitive`, its `inputs` each with a digest scope,
`seed` when its primitive is random, a `status` rule naming the output field that holds the status, and `grants` for
check and derived steps. `config check` SHALL refuse a step whose primitive or scope does not exist.

#### Scenario: A step from YAML alone
- **WHEN** a local pack declares a step over an existing primitive, with no Python
- **THEN** `veriphy layers step <step>` runs it and writes a record

#### Scenario: An unknown primitive
- **WHEN** a step names the primitive `lean.chek`
- **THEN** `config check` fails, naming the step and the primitive

### Requirement: Digest scopes
Each input's content in the digest SHALL be given by its scope: `value`, `file`, `files`, or a scope a pack defines in
its own code. The `lean` pack SHALL define `lean-imports`: the file, every workspace file it imports, the toolchain and
the manifest.

#### Scenario: Unrelated edit
- **WHEN** a Lean file that `Claim.lean` does not import changes
- **THEN** `veriphy layers step check Claim.lean` replays its record

#### Scenario: Imported edit
- **WHEN** a workspace file that `Claim.lean` imports changes
- **THEN** `check Claim.lean` gets a new digest and runs

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

### Requirement: Agent steps
An agent step SHALL record the artifact it names, by digest, with its author and the status `written`, and SHALL run
no primitive.

#### Scenario: A formalization
- **WHEN** `veriphy layers step record-statement Claim.lean --by agent` runs
- **THEN** a record under `.veriphy/runs/formalize/` holds the file's digest and the author `agent`

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

### Requirement: Accepted statuses
A step MAY name the statuses that mean success with `accepts`. Any other status SHALL then be recorded as `refused`,
with the tool's word kept as `result`. `config check` SHALL refuse a step that grants a level over a primitive whose
statuses include words Veriphy doesn't know when the step names no `accepts`, and SHALL refuse any unknown field of a
step or of an input.

#### Scenario: A tool's own words
- **WHEN** a step with `accepts: [found]` runs a tool that answers `missing`
- **THEN** the record's status is `refused`, its `result` is `missing`, and no level is granted
