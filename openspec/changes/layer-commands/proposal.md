# Proposal

## Why

`veriphy --help` lists twenty commands in one flat list: the steps of every selected pack, the layers' programs and
two of the `math` pack's programs side by side. The list grows with every pack, and nothing in it says which layer a
command belongs to. The package is organized by layer; its command should be too.

## What Changes

- **BREAKING** The `veriphy` command has four commands:
  - `veriphy layers <layer> …`, one group per layer in layer order: `primitive` (0), `step` (1), `claims` (2),
    `workflow` (3), `agents` (4);
  - `veriphy config show|check`;
  - `veriphy pack list|<pack> <program> …`, the selected packs and their programs;
  - `veriphy help`.
- **BREAKING** Steps run as `veriphy layers step <name> …`; `veriphy layers step list` replaces `veriphy steps`, and
  `veriphy layers step records` replaces `veriphy records`. Workflows run as `veriphy layers workflow next|run`, with
  `list` new.
- **BREAKING** A pack's own programs run as `veriphy pack <pack> <program>`: `veriphy pack math certificates …` and
  `veriphy pack math translations …`. A pack declares them in a `commands` section of its `pack.yaml`, so the command
  no longer lists programs by hand. `veriphy pack list` lists the selected packs.
- A step cannot be named `list` or `records`: `config check` refuses it.
- `veriphy.run(verb, …)` in Python and `veriphy <verb>`/`#veriphy <verb>` in Lean are unchanged.
- The README and the docs present Veriphy as a framework whose packs bring each field: the guide covers the
  framework, and a Packs section covers `math`, `lean` and `reproduction`. The docs, skills, playbooks, CI and tests use
  the grouped commands.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `core/operations`: the shell spelling of an operation is `veriphy layers step <verb>`, and the group is by layer.
- `core/steps`: `veriphy layers step list` replaces `veriphy steps`; reserved step names.
- `core/step-records`: `veriphy layers step <name>` and `veriphy layers step records`.
- `core/workflows`: `veriphy layers workflow next|run|list`.
- `core/workspace-config`: a pack's `commands` section.

## Impact

- `veriphy.__main__`, `veriphy.steps._cli`, `veriphy.workflows._cli`, `veriphy.core._config` (schema and checks).
- `pack.yaml` of the `math` pack.
- Skills, playbooks, the user guide, the architecture doc, CI and the tests that run commands.
- Depends on `remove-old-api`, whose shell spelling it changes.
