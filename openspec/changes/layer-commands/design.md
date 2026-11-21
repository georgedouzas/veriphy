# Design

## Context

`veriphy.__main__` builds one click group from three sources: the workspace's steps (`StepGroup`), its own commands
(`records`, `steps`, `help`) and a hand-written `PROGRAMS` table of lazily imported groups.

## Decisions

- **Three groups at the top.** `layers`, `config` and `pack` (and `help`) keep the top level fixed as packs are added:
  what a pack adds appears under `layers step`, `layers workflow` or `pack <name>`, never beside the groups.

- **Steps under `step`.** `StepGroup` becomes the `step` group, with `list` and `records` as its own commands. Its
  commands still come from the workspace that the top-level `--root` names, read from the click context's parent.
- **Layer groups stay lazy.** The `layers` group keeps a table of the five layer groups and `config`, imported when
  named, since `claims` needs the graph extra and pack programs may import Sage; `--help` lists them without importing.
- **Pack programs from `pack.yaml`.** A pack declares `commands: {certificates: {command: module:attr, help: …}}`. The
  `pack` group adds one group per selected pack that declares commands, named as the pack, whose subcommands are
  imported when named. The resolved configuration already records which pack gave each entry, so the commands are
  grouped by that source. This replaces `PROGRAMS` for `certificates` and `translations`, and lets any pack add programs.
- **Reserved names.** `list` and `records` in `step`, `list`, `next`, `run` in `workflow`, and `list` in `pack` are the
  groups' own; `config check` refuses a step named `list` or `records`, so a pack cannot hide them.
- **`--root` is eager.** `--help` is processed before other options, so `--root` is marked eager too, and the help
  lists the packs of the workspace given.
- **Python and Lean unchanged.** `veriphy.run("check", …)` and `#veriphy check` name the operation alone: the group
  is only how the shell lists them.

## Risks

- Scripts and skills that call `veriphy check …` or `veriphy next …` break; the release notes list the renames, and
  every in-repo caller moves in this change.
