# Tasks

## 1. Pack and primitives

- [ ] 1.1 Write `packs/reproduction/pack.yaml` with the tool, primitives, steps, levels, convention aspect and workflow, requiring only `core`. Verify with `config check` on a workspace with `packs: [core, reproduction]`, and with pytest that `config show` lists them and no Lean or SageMath entry (D5).
- [ ] 1.2 Add the example: a small public dataset with its hash, an R regression script and a claim file. Verify by running the script in the pinned image and comparing its estimate with the claim.
- [ ] 1.3 Add `r.run` with the data-hash check, and the composite `r.robustness` (D1, D3). Verify with pytest using fake files tools, and with the example in the pinned image, skipped without a container runtime: a changed hash refuses to start R, and one flipping variation is named.

## 2. Steps and claims

- [ ] 2.1 Declare `reproduce` with `compare`, and `robustness` (D2). Verify with pytest on fake tools: agreeing grants `reproduced`, differing grants nothing and records both estimates, and all variations holding grants `robust`.
- [ ] 2.2 Check that a reproduce record gives the claim its own level, and that a clash on `identification` is found (D4). Verify with graph tests: a claim reaches `reproduced (reproduction)` in the level report, and two claims assuming exclusive conventions clash.

## 3. Playbook and integration

- [ ] 3.1 Write the `reproduce` playbook and skill. Verify with the document tests: every command named exists, and the skill's two copies are identical.
- [ ] 3.2 Add a CI job that runs the example in the pinned image, and run the gate. Verify that every session and job is green.

## Workflow follow-up

- Archive, and release as a minor version.
