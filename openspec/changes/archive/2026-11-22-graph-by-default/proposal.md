# Proposal

## Why

The claim graph is where every pack's evidence meets: a reproduced estimate and a Lean proof cap each other there. As
an optional extra (`veriphy[graph]`) it was a second install step that every guide had to explain, and a missing extra
was a failure mode of its own. A workspace without Lean, such as one of the `reproduction` pack, also had no marker of
its root, so Veriphy walked up to an enclosing Lean workspace and used its packs.

## What Changes

- **BREAKING** The `graph` extra goes: `pyoxigraph`, `pyshacl` and `rdflib` are dependencies of every install, and
  `pip install veriphy` (or `sage -pip install veriphy`) is the only install step. The reasoner and the checker are
  still set up on first use from the pinned release.
- The error for a reasoner that is not set up names the command that sets it up, not an extra to install.
- `veriphy.yaml` marks a workspace root, as a lakefile does: the root is the nearest directory, upwards, holding either.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `research/certified-graph-reasoning`: setup needs no extra.
- `research/research-workflow`: the skill needs no extra.
- `certificates/project-layout`: `veriphy.yaml` marks the root.

## Impact

- `pyproject.toml`, `uv.lock`, the nox `tests` session and CI drop `--extra graph`.
- `veriphy.core` (the root and the error), `veriphy.primitives.graph._engine`, the research skill and playbook, the
  README, the guide and the constitution.
