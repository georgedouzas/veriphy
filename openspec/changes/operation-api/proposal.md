# Proposal

## Why

Veriphy has three calling conventions and many names for one idea. Lean has `sage_run`, `sage_test` and seven
`#veriphy_*` commands; the shell has `python -m veriphy <step>`, `python -m veriphy.graph` and
`python -m veriphy.prompts`; and a Sage script fills in globals the daemon injects and sets a variable named `proof`.
Everything Veriphy runs is the same thing, an operation with a verb, a target, inputs and a result, and it should be
called the same way everywhere.

## What Changes

- **Operations and verbs.** An operation is a verb, a target, typed inputs and a result `{status, outputs, level,
  record}`. The verbs are `formalize`, `extract`, `check`, `meaning`, `search`, `certify`, `test`, `level`,
  `translate`, `export`, `validate`, `reason`, `report`, `reproduce` and `vary`, and a pack can add more.
- **Lean: one tactic and one command.** `veriphy <verb> …` acts on the goal (`veriphy certify "sos.sage"`), and
  `#veriphy <verb> …` acts on a named claim or the project (`#veriphy meaning c`, `#veriphy test c "…"`,
  `#veriphy level`, `#veriphy export`, `#veriphy translate e`, `#veriphy translations`, `#veriphy coverage`,
  `#veriphy check-translations`, `#veriphy help`).
- **Shell: one command.** `veriphy <verb> <target> [inputs]`, the same as `python -m veriphy <verb>`, with
  `veriphy help`, `veriphy claims …` (was `python -m veriphy.graph`), `veriphy agents …` (was
  `python -m veriphy.prompts`), `veriphy records`, `veriphy certificates` and `veriphy translations`. `elaborate`
  becomes `check`.
- **Python: one function.** `veriphy.run(verb, target, **inputs) -> Result`.
- **One script contract.** A script has a header `SCRIPT = {"name", "serves", "inputs"}` and an entry point
  `run(goal, inputs)` returning `found(...)`, `refuted(...)` or `unknown(reason)` from `veriphy.script`, which also
  exports `Goal`. A one-line script in Lean is the body of `run`. The recipe templates move to this form.
- **Deprecations.** `sage_run`, `sage_test`, the `#veriphy_*` commands, `elaborate`, the old `python -m` programs and
  scripts that set `proof` keep working for one minor release, each warning with its new form.

Depends on `layered-modules`.

## Capabilities

### New Capabilities

- `core/operations`: operations, verbs, results, the Lean tactic and command, the shell command, `veriphy.run`, the
  script contract and the deprecations.

### Modified Capabilities

None. The existing specs name the old forms, which keep working; the archive of this change records the new names.

## Impact

- Lean: a `veriphy` tactic and a `#veriphy` command dispatching on the verb, over today's elaborators; deprecated
  syntax for the old names.
- Python: `veriphy.run` and `Result`, the `veriphy` console script, verb aliases in the step command, the script
  contract in `veriphy.script` and the daemon's script runner.
- The recipe templates, playbooks, skills, user guide and Lean tests use the new forms.
