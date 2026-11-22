# Tasks

## 1. Packs

- [x] 1.1 Apply the framework pack to every workspace unnamed, move the `lean` pack into `math`, with the Lean library
  and its Lake files, and point CI and the tests at the new workspace.
- [x] 1.2 Replace `reproduction` with `social-science`: the analysis in Python, `check-concepts`, the conventions, the
  playbook and the skill.
- [x] 1.3 Add `{pack}` to tool commands, import local packs' Python, and accept dashes in pack names.

## 2. Layout

- [x] 2.1 Move the skills into their packs and name them in the plugin manifest; move the examples into
  `docs/examples/`; turn the scripts into the nox sessions `diagrams`, `tables` and `bundle`.
- [x] 2.2 Rewrite the packs pages, with the economics and history examples, and the social-science page.

## 3. Gate

- [x] 3.1 Run the gate and CI. Verify that every session and job is green.
