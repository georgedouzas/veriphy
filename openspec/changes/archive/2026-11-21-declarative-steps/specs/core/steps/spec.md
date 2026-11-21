# Spec Delta

## ADDED Requirements

### Requirement: Step declarations
A step SHALL be declared in the config with its `kind`, its `primitive`, its `inputs` each with a digest scope,
`seed` when its primitive is random, a `status` rule naming the output field that holds the status, and `grants` for
check and derived steps. `config check` SHALL refuse a step whose primitive or scope does not exist.

#### Scenario: A step from YAML alone
- **WHEN** a local pack declares a step over an existing primitive, with no Python
- **THEN** `veriphy <step>` runs it and writes a record

#### Scenario: An unknown primitive
- **WHEN** a step names the primitive `lean.chek`
- **THEN** `config check` fails, naming the step and the primitive

### Requirement: Digest scopes
Each input's content in the digest SHALL be given by its scope: `value`, `file`, `files`, or a scope a pack defines in
its own code. The `lean` pack SHALL define `lean-imports`: the file, every workspace file it imports, the toolchain and
the manifest.

#### Scenario: Unrelated edit
- **WHEN** a Lean file that `Claim.lean` does not import changes
- **THEN** `veriphy check Claim.lean` replays its record

#### Scenario: Imported edit
- **WHEN** a workspace file that `Claim.lean` imports changes
- **THEN** `check Claim.lean` gets a new digest and runs

### Requirement: Comparison
A step MAY declare `compare` with an output `field`, an input `against` and a `tolerance`, and its status SHALL then be
`agrees` when the two values differ by at most the tolerance and `differs` otherwise, with both values recorded.

#### Scenario: Within tolerance
- **WHEN** the output's `estimate` is 0.4213 and the claimed value 0.4210, with tolerance 0.001
- **THEN** the status is `agrees`, and the record holds both values

### Requirement: Agent steps
An agent step SHALL record the artifact it names, by digest, with its author and the status `written`, and SHALL run
no primitive.

#### Scenario: A formalization
- **WHEN** `veriphy formalize Claim.lean --by agent` runs
- **THEN** a record under `.veriphy/runs/formalize/` holds the file's digest and the author `agent`

### Requirement: Steps command
`veriphy steps` SHALL list the workspace's steps with their kind, primitive and pack, and
`veriphy <step>` SHALL take one argument or option per declared input.

#### Scenario: Listing
- **WHEN** `veriphy steps` runs with the default config
- **THEN** it lists `check` and `level` from `lean`, `meaning` from `math`, and `validate`, `reason` and `report`
  from `core`
