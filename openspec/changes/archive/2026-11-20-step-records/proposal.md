# Proposal

## Why

Veriphy's results are scattered and shaped differently: Lean messages, test records in `.veriphy/tests/`, graph runs
in `.veriphy/graph/runs/`, and nothing at all for some steps. An agent has to know five Python commands, thirteen Lean
commands and six daemon methods, and read each one's output in its own format. Nothing guarantees that running a step
twice on the same inputs gives the same answer. This is the first milestone of the architecture in
`docs/architecture/index.md`: every effect becomes a step with hashed inputs and a recorded output.

## What Changes

- A step record format, written to `.veriphy/runs/<step>/<digest>.json`, with the step, its kind, the input digest,
  the tool versions, the seed, the status, the outputs and the level when the step grants one.
- A step runner: a step whose input digest already has a record returns that record without running anything.
  `--rerun` runs it again and reports whether the output changed.
- One command, `python -m veriphy <step>`, with the first steps: `elaborate`, `level`, `validate`, `reason` and
  `report`. `python -m veriphy records` lists and shows records.
- The Lean steps run Lean through `lake env lean` from the workspace, so they need no editor.
- `reason` keeps its certificate directory and writes a step record that points to it. The existing commands
  (`python -m veriphy.graph …`, `#veriphy_levels`) keep working.

## Capabilities

### New Capabilities

- `core/step-records`: the record format, the digest, the runner, the step kinds and the `python -m veriphy` command.

### Modified Capabilities

None.

## Impact

- New: `veriphy.core` (records, digest, store), `veriphy.steps` (runner and the five steps), `veriphy/__main__.py`.
- `veriphy.graph`: `reason`, `validate` and `appendix` are called by the steps, unchanged.
- Docs: the user guide gains the step command, and the architecture page links this change.
- Later changes build on it: `meaning-step`, `workspace-config`, `tool-contracts`, `reproduction-pack`,
  `workflows-as-data`.
