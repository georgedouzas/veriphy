# Tasks

## 1. Commands

- [x] 1.1 Make the steps the `step` group, with `list` (replacing `steps`) and `records`, and refuse a step named
  `list` or `records` in `config check`.
- [x] 1.2 Add the `workflow` group with `list`, `next` and `run`.
- [x] 1.3 Add the `commands` section to the pack schema, declare `certificates` and `translations` in the `math`
  pack, and group a selected pack's programs under `veriphy pack <pack>`, with `veriphy pack list`.
- [x] 1.4 Make the top level `layers` (the layer groups, in order), `config`, `pack` and `help`.

## 2. Callers and gate

- [x] 2.1 Move every caller to the grouped commands: the skills, the playbooks, the architecture doc, `veriphy help`,
  CI and the tests.
- [x] 2.2 Rewrite the README and the docs around the framework: the guide for concepts, configuration, commands,
  steps, levels, workflows, the claim graph and writing a pack; a Packs section for `math`, `lean` and
  `reproduction`; the package and plugin descriptions.
- [x] 2.3 Run the gate and CI. Verify that every session and job is green.
