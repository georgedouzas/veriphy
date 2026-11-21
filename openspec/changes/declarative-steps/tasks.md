# Tasks

## 1. Declarations

- [ ] 1.1 Add step declarations to the steps registry and build steps from them in the runner, with the status rule and `config check` for unknown primitives and scopes (D1). Verify with pytest: a fixture pack's YAML-only step runs and records, and an unknown primitive or scope is refused with its name.
- [ ] 1.2 Add the scopes `value`, `file` and `files`, pack-defined scopes by import path, and `lean-imports` in the `lean` pack (D2). Verify with pytest on a fixture workspace: an unrelated edit replays, an imported edit runs, and a toolchain change runs.
- [ ] 1.3 Add `compare` (D3). Verify with pytest: within and beyond the tolerance, both values recorded.
- [ ] 1.4 Add agent steps (D4). Verify with pytest: `formalize` records the artifact's digest and author, and a changed artifact gives a new record.

## 2. Packs and command

- [ ] 2.1 Declare `check`, `level`, `meaning`, `validate`, `reason` and `report` in their packs and delete their Python definitions, keeping only scopes and composites. Verify with the step tests unchanged apart from digests.
- [ ] 2.2 Generate `veriphy <step>` from declarations, and add `veriphy steps` (D5). Verify with pytest on the parser: required inputs are positional, others options, and `steps` lists each with its pack.

## 3. Integration

- [ ] 3.1 Document step declarations and scopes in the user guide, and run the gate and CI. Verify that every session and job is green.

## Workflow follow-up

- Archive, and release as a minor version.
