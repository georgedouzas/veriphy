# Tasks

## 1. Files and packs

- [x] 1.1 Add `veriphy.core.config` with the schema, loading and validation of `veriphy.yaml` and `pack.yaml` (D1). Verify with pytest: no file resolves to `packs: [math]`, an unknown key fails naming it, and a wrong type fails with its path.
- [x] 1.2 Add packs by name and by path, ordered by `requires` (D2, D3). Verify with pytest on fixture packs: requirements are loaded first, an unknown pack name is an error, and a pack requiring a missing pack names it.
- [x] 1.3 Add the merge as JSON Merge Patch (RFC 7396) and the collision check (D3, D4). Verify with pytest: the RFC's own examples, later values win, `null` removes, unrelated packs defining one entry fail with both names, and the workspace file settles it.

## 2. Registries and commands

- [x] 2.1 Build the primitive registry and the steps from the resolved config's sections (D5). Verify with pytest: `packs: [core]` hides the `sage.*` primitives, and `tools: {sage: null}` reports them unavailable.
- [x] 2.2 Add `config show` with the source of each entry, and `config check` with the schema and the references between sections. Verify with pytest: each entry names its pack or file, and a primitive naming an undeclared tool is refused.
- [x] 2.3 Put the config digest into every step's input digest (D6). Verify with pytest: a changed pin gives a new digest, and a changed comment does not.

## 3. Integration

- [ ] 3.1 Document `veriphy.yaml`, `pack.yaml` and the two commands in the user guide, and run the gate and CI. Verify that every session and job is green.

## Workflow follow-up

- Archive, and release as a minor version.
