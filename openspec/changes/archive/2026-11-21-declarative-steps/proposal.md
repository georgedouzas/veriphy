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
- **Today's steps that wrap a primitive become declarations.** `check` and `level` in `lean`, `meaning` in `math`,
  with the same records apart from the narrower Lean digests. The graph steps (`validate`, `reason`, `report`) stay
  Python steps of `veriphy.claims`, registered by `core`: they load and write the claim graph, which is layer-2 work,
  and a step's code lives at the highest layer it needs.

Depends on `packs-and-config`.

## Capabilities

### New Capabilities

- `core/steps`: step declarations, digest scopes, status and comparison rules, agent steps and the generated command.

### Modified Capabilities

- `core/step-records`: the input digest covers each input's scope, and the first steps are declared in packs.

## Impact

- `veriphy.steps`: the runner builds steps from declarations. The Lean steps in `veriphy.packs.lean.steps` and
  `meaning` in `veriphy.packs.math.steps` shrink to their declarations and a scope.
- Packs: step entries in `core`, `lean` and `math`; `lean-imports` in the `lean` pack's module.
- Records: Lean steps get new digests once, when this change lands.
