# Tasks

## 1. Pack

- [ ] 1.1 Write `packs/reproduction/pack.yaml` with the tool, levels, convention aspect and workflow. Verify with `config check` on a workspace that selects it, and with pytest that `config show` lists them.
- [ ] 1.2 Add the example: a small public dataset with its hash, an R regression script and a claim file. Verify by running the script in the pinned image and comparing its estimate with the claim.

## 2. Steps

- [ ] 2.1 Add `reproduce` with the data-hash check and the estimate comparison (D1, D2). Verify with pytest using a fake files tool, and with the example in the pinned image, skipped without a container runtime: a match grants `reproduced`, a changed hash refuses to run.
- [ ] 2.2 Add `test` over declared variations (D3). Verify with pytest: all variations holding grants `robust`, and one flipping keeps `reproduced` and names it.
- [ ] 2.3 Check that a clash on `identification` is found by the graph checks (D4). Verify with a graph test of two claims assuming exclusive conventions.

## 3. Playbook and integration

- [ ] 3.1 Write the `reproduce` playbook and skill. Verify with the document tests: every command named exists, and the skill's two copies are identical.
- [ ] 3.2 Add a CI job that runs the example in the pinned image, and run the gate. Verify that every session and job is green.

## Workflow follow-up

- Archive, and release as a minor version.
