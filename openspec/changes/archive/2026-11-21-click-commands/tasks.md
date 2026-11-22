# Tasks

## 1. Commands

- [x] 1.1 Add `click`, and define the `veriphy` group with the layers' and packs' commands: `claims`, `agents`, `primitive`, `config`, `records`, `certificates`, `translations` (D1). Verify with click's `CliRunner`: each command's outputs and exit statuses are those of the old program, and `python -m veriphy` runs the group.
- [x] 1.2 Build a command per registered step from its `Argument`s, for the workspace's packs (D2, D3). Verify with pytest: `veriphy meaning --help` lists its options, a step's exit statuses are unchanged, and a workspace of `core` alone has no `check` command.
- [x] 1.3 Remove the dispatcher and every `argparse` parser, keeping the old `python -m veriphy.<module>` programs on the same commands. Verify that no module imports `argparse`, and the alias tests pass.

## 2. Integration

- [x] 2.1 Run the gate and CI. Verify that every session and job is green.

## Workflow follow-up

- Archive with `packs-and-config`, and release as a minor version.
