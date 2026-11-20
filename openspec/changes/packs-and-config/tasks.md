# Tasks

## 1. Files and packs

- [ ] 1.1 Add `veriphy.config` with the schema, loading and validation of `veriphy.yaml` and `pack.yaml` (D1). Verify with pytest: no file resolves to `packs: [math]`, an unknown key fails with its line, and a wrong type fails with its path.
- [ ] 1.2 Add packs by name and by path, ordered by `requires` (D2, D3). Verify with pytest on fixture packs: requirements are loaded first, an unknown pack name is an error, and a pack requiring a missing pack names it.
- [ ] 1.3 Add the merge with `null` removal and the collision check (D3, D4). Verify with pytest on layered fixtures: later values win, `null` removes, unrelated packs defining one entry fail with both names, and the workspace file settles it.

## 2. Registries and commands

- [ ] 2.1 Split the resolved config into one registry per layer, and have `veriphy.primitives` take its registry from it (D5). Verify with pytest: `packs: [core]` hides the `sage.*` primitives, and `tools: {sage: null}` reports them unavailable.
- [ ] 2.2 Add `config show` with sources and `config check` running each layer's registered checks. Verify with pytest: each value names its pack or file, and a check registered by a fixture layer runs.
- [ ] 2.3 Put the config digest into every step's input digest (D6). Verify with pytest: a changed pin gives a new digest, and a changed comment does not.

## 3. Integration

- [ ] 3.1 Document `veriphy.yaml`, `pack.yaml` and the two commands in the user guide, and run the gate and CI. Verify that every session and job is green.

## Workflow follow-up

- Archive, and release as a minor version.
