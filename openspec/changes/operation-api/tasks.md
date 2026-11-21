# Tasks

## 1. Python

- [ ] 1.1 Add `Result` and `veriphy.run`, the `veriphy` console script, `veriphy help`, and the verbs as step names with `check` for `elaborate`; route `claims`, `agents`, `records`, `certificates` and `translations` through `veriphy` (D2). Verify with pytest: `veriphy.run` and the shell give the same record, `help` lists the verbs, and each old program and `elaborate` warn and still work.
- [ ] 1.2 Add the script contract to `veriphy.script` and the daemon's script runner: `SCRIPT`, `run(goal, inputs)`, `found`, `refuted`, `unknown`, inline bodies, and the deprecated `proof` form (D3, D4). Verify with the oracle script tests extended to each result kind, an inline body, and a legacy script that warns.

## 2. Lean

- [ ] 2.1 Add the `veriphy` tactic (`certify`, `search`) and the `#veriphy` command (`meaning`, `test`, `level`, `export`, `translate`, `translations`, `coverage`, `check-translations`, `help`) over today's elaborators, with the old names as deprecated syntax (D1, D5). Verify with Lean tests of each verb, and one test per old name showing it works and warns.
- [ ] 2.2 Rewrite the recipe templates to the script contract, and the Lean tests to the new forms. Verify with the Lean test suite.

## 3. Integration

- [ ] 3.1 Update the playbooks, skills, user guide and README to the new forms, and run the gate and CI. Verify with the document tests (every named verb and command exists) and every session and job green.

## Workflow follow-up

- Archive, and release as a minor version with `layered-modules`.
