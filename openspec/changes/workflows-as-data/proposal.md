# Proposal

## Why

The playbooks describe their step sequences in prose, so two agents can follow the same playbook differently, and no
tool can say what should happen next. With every step recorded, the next step is a function of the records. Writing
workflows as data makes that function explicit, and lets the skills shrink to the parts only an agent can do.

## What Changes

- A workflow schema in the config: an ordered list of steps, each with optional transitions on its status
  (`{counterexample: stop}`, `{rejected: search}`), an attempt limit and a condition.
- `veriphy next <workflow> <target>` prints the next step from the records, the same every time for the
  same records.
- `veriphy run <workflow> <target>` runs steps until one needs the agent, then stops and says which.
- The `math` pack defines `prove-claim` and `verify-paper`, the `reproduction` pack `reproduce-analysis`.
- A pack adds workflows in its `pack.yaml`, and a workspace can override or add one in `veriphy.yaml`.
- The skills (layer 4) follow `next`, and the playbooks keep only the guidance for agent steps: formalizing,
  extracting, writing scripts.

Workflows are layer 3: they use steps (layer 1) and read what the records establish (layer 2), and add nothing
below. Depends on `declarative-steps` and `claims-and-trust`, and on `reproduction-pack` for its workflow.

## Capabilities

### New Capabilities

- `core/workflows`: the schema, `next`, `run` and the default workflows.

### Modified Capabilities

None.

## Impact

- New: `veriphy.steps` workflow engine.
- Playbooks and skills: `prove`, `certify`, `research`, `reproduce`.
- Packs: workflow definitions in `math` and `reproduction`.
