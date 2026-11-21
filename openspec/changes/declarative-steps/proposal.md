# Proposal

## Why

Steps are layer 1: a primitive, the inputs its digest covers, and a record. Today each step is hand-written Python in
`veriphy.steps`, so a field cannot add one without code, and the Lean steps hash every Lean file of the workspace, so
editing any file invalidates every Lean record.

## What Changes

- **Steps are declared.** A step entry in the config names its `kind`, its `primitive`, its `inputs` with a digest
  scope each, whether it takes a seed, how its status comes from the primitive's output, and, for check and derived
  steps, the levels it may grant. An optional `compare` sets the status by comparing an output field with an input
  within a tolerance.
- **Digest scopes.** A scope says what content an input stands for: `value` (the value itself), `file` (the file's
  bytes) and `files` (a directory's files). A pack can add scopes in its own code. The `lean` pack adds
  `lean-imports`: a Lean file, every workspace file it imports, the toolchain and the manifest.
- **Agent steps are recorded.** An agent step (`formalize`, `extract`) records the artifact it names, by digest, with
  who wrote it, so later steps and workflows can refer to it.
- **One runner, one command.** The step runner builds every step from the steps registry, and
  `veriphy <step>` takes one argument or option per declared input. `veriphy steps` lists them.
- **Today's steps move to their packs.** `check` and `level` to `lean`, `meaning` to `math`, `validate`, `reason`
  and `report` to `core`, with the same records apart from the narrower Lean digests.

Depends on `packs-and-config`.

## Capabilities

### New Capabilities

- `core/steps`: step declarations, digest scopes, status and comparison rules, agent steps and the generated command.

### Modified Capabilities

- `core/step-records`: the input digest covers each input's scope, and the first steps are declared in packs.

## Impact

- `veriphy.steps`: the runner reads declarations. The Lean steps in `veriphy.packs.lean.steps`, `meaning` in
  `veriphy.packs.math.steps` and the graph steps in `veriphy.claims` shrink to scopes and composites.
- Packs: step entries in `core`, `lean` and `math`; `lean-imports` in the `lean` pack's module.
- Records: Lean steps get new digests once, when this change lands.
