# core/operations Specification

## Purpose
Call everything Veriphy runs the same way from every surface: an operation is a verb, a target, typed inputs and a result, run by the `veriphy` tactic and `#veriphy` command in Lean, `veriphy layers step <verb>` in the shell and `veriphy.run` in Python, with one contract for scripts in any language.

## Requirements

### Requirement: Operations
Every operation Veriphy runs SHALL have a verb, a target, typed inputs and a result with `verb`, `target`, `status`,
`outputs`, `level` and `record`. The verbs SHALL be `formalize`, `extract`, `check`, `meaning`, `search`, `certify`,
`test`, `level`, `translate`, `export`, `validate`, `reason`, `report`, `reproduce` and `vary`, and a pack MAY add
verbs.

#### Scenario: Listing the verbs
- **WHEN** a user runs `veriphy help`
- **THEN** it lists every verb of the workspace with its kind and one line on what it does

### Requirement: Lean tactic and command
Lean SHALL provide one tactic, `veriphy <verb> …`, acting on the current goal, and one command, `#veriphy <verb> …`,
acting on a named claim or the project, and `#veriphy help` SHALL list the verbs available in Lean.

#### Scenario: Certifying a goal
- **WHEN** a proof runs `veriphy certify "sos.sage"` on `2 * a * b ≤ a ^ 2 + b ^ 2`
- **THEN** it closes the goal as `veriphy certify "sos.sage"` did, at level `certificate`

#### Scenario: Testing a claim's meaning
- **WHEN** a file runs `#veriphy sample wrong` on `∀ x : ℝ, 0 ≤ x → √(x ^ 2) = -x`
- **THEN** it reports the counterexample at `x := 1` as `#veriphy sample wrong` did

### Requirement: Shell command and Python function
`veriphy layers step <verb> <target> [inputs]` SHALL run the verb's step, the same as `python -m veriphy layers step <verb>`, and
`veriphy.run(verb, target, **inputs)` SHALL return the same result as a `Result`.

#### Scenario: Same result from both
- **WHEN** `veriphy layers step check Claim.lean` and `veriphy.run("check", "Claim.lean")` run on one file
- **THEN** both give the same status and the same record

#### Scenario: Help generated from a step
- **WHEN** a user runs `veriphy layers step sample --help`
- **THEN** it lists the step's arguments and options, `--seed`, `--values`, `--points` and `--informal` among them

### Requirement: One click group
The `veriphy` command SHALL be one click group with four commands: `layers`, which holds one group per layer in layer
order (`primitive`, `step`, `claims`, `workflow`, `agents`); `config`; `pack`, which lists the selected packs and holds
one group per selected pack that declares programs; and `help`. It SHALL list the layer and pack groups without
importing their modules.

#### Scenario: The top level
- **WHEN** a user runs `veriphy --help` with the default config
- **THEN** it lists `config`, `help`, `layers` and `pack`, and nothing else

#### Scenario: The layers
- **WHEN** a user runs `veriphy layers --help`
- **THEN** it lists `primitive`, `step`, `claims`, `workflow` and `agents`, in that order

#### Scenario: A pack's step is a command
- **WHEN** a workspace uses the `social-science` pack and a user runs `veriphy layers step --help`
- **THEN** `reproduce` and `vary` are listed beside the other steps, `list` and `records`

### Requirement: Script contract
A script SHALL declare `SCRIPT` with its `name`, the verb it `serves` and its `inputs`, and define
`run(goal, inputs)` returning `found(...)`, `refuted(...)` or `unknown(reason)` from `veriphy.script`. A script given
inline SHALL be the body of `run`, with `goal` and `inputs` bound.

#### Scenario: A template
- **WHEN** the `calc_derivation` template is used by `veriphy certify`
- **THEN** its `run` returns `found` with the calc proof, and the goal closes

#### Scenario: Refuted
- **WHEN** a script for `certify` returns `refuted({"x": "2"})`
- **THEN** the tactic fails, reporting that the goal is false at `x := 2`

### Requirement: One spelling per operation
Each operation SHALL have one spelling in each place it runs: `veriphy <verb>` and `#veriphy <verb>` in Lean,
`veriphy layers step <verb>` in the shell and `veriphy.run` in Python. The removed names SHALL fail as unknown, not run.

#### Scenario: An old tactic
- **WHEN** a proof runs `sage_run file "sos.sage"`
- **THEN** Lean reports unknown syntax, and `veriphy certify "sos.sage"` closes the goal

#### Scenario: An old verb
- **WHEN** a user runs `veriphy layers step elaborate Claim.lean`
- **THEN** the command fails as an unknown command, listing the steps

#### Scenario: A script that assigns its result
- **WHEN** a script for `certify` assigns `proof = Lean.tactic("rfl")` and defines no `run`
- **THEN** the Sage session refuses it, saying to return `found(proof)` from `run(goal, inputs)`

#### Scenario: A request without JSON-RPC
- **WHEN** the Sage session receives `{"id": 1, "method": "ping"}`
- **THEN** it answers with the JSON-RPC 2.0 error code -32600 (invalid request)
