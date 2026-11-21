# Tasks

## 1. Python

- [x] 1.1 Remove the alias packages `veriphy.toolkit`, `graph`, `oracle`, `prompts`, `sage_server`, `certificates` and
  `translations`, and `alias`/`run_alias` from `veriphy.core._aliases`; delete `tests/test_aliases.py` and move every
  remaining import to the new paths.
- [x] 1.2 Remove `DEPRECATED_VERBS` and the `elaborate` handling from `veriphy.steps`.
- [x] 1.3 Refuse scripts that assign their result instead of returning from `run(goal, inputs)`, and answer requests
  without `"jsonrpc": "2.0"` with -32600.

- [x] 1.4 Remove the per-group entry points (`__main__` modules and `main()` functions) and the 0.1.0 certificates
  layout, moving their tests onto the `veriphy` command.

- [x] 1.5 Keep no process between calls: Sage as a `files` tool, run once per call; Lean as `lake env lean` once per
  call; remove the `jsonrpc` contract, its session client, the Lean REPL and the `veriphy-sage-server` script.

- [x] 1.6 Call the Sage process the Sage session everywhere: the module, the variable, the specs and the docs.

## 2. Lean

- [x] 2.1 Make `veriphy certify`, `#veriphy test`, `#veriphy meaning`, `#veriphy translations check` and the Sage-free
  `#veriphy` verbs elaborate directly, and delete the old syntaxes, `Kit/Deprecation.lean` and
  `VeriphyTest/Deprecated.lean`.

## 3. Docs and gate

- [x] 3.1 Use only the current names in the docs, the specs, the skills, the saved certificates and the tests, and list
  the renames in the commit's `BREAKING CHANGE` footer, from which the changelog is generated.
- [ ] 3.2 Run the gate and CI. Verify that every session and job is green.
