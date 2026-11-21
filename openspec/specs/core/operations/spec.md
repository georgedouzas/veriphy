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
- **WHEN** a file runs `#veriphy meaning wrong` on `∀ x : ℝ, 0 ≤ x → √(x ^ 2) = -x`
- **THEN** it reports the counterexample at `x := 1` as `#veriphy meaning wrong` did

### Requirement: Shell command and Python function
`veriphy <verb> <target> [inputs]` SHALL run the verb's step, the same as `python -m veriphy <verb>`, and
`veriphy.run(verb, target, **inputs)` SHALL return the same result as a `Result`. `veriphy layers claims`, `veriphy layers agents`,
`veriphy layers step records`, `veriphy layers primitive`, `veriphy config`, `veriphy pack math certificates` and `veriphy pack math translations` SHALL
replace the per-module programs.

#### Scenario: Same result from both
- **WHEN** `veriphy layers step check Claim.lean` and `veriphy.run("check", "Claim.lean")` run on one file
- **THEN** both give the same status and the same record

#### Scenario: Help generated from a step
- **WHEN** a user runs `veriphy layers step meaning --help`
- **THEN** it lists the step's arguments and options, `--seed`, `--values`, `--points` and `--informal` among them

### Requirement: One click group
The `veriphy` command SHALL be one click group, whose subcommands the layers and packs contribute, with a command per
registered step of the workspace.

#### Scenario: A pack's step is a command
- **WHEN** a workspace uses the `reproduction` pack and a user runs `veriphy --help`
- **THEN** `reproduce` and `vary` are listed beside the layers' commands

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

### Requirement: Deprecated forms
`veriphy certify`, `sage_test`, the `#veriphy_*` commands, the step name `elaborate`, the `python -m veriphy.<module>`
programs and scripts that set `proof` SHALL keep working for one minor release, each warning once with its new form.

#### Scenario: An old tactic
- **WHEN** a proof runs `veriphy certify "sos.sage"`
- **THEN** it closes the goal, and a warning says to use `veriphy certify "sos.sage"`
