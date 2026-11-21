# Design

## Context

After `packs-and-config`, `veriphy.__main__` maps the first argument to a program (`claims`, `agents`, `primitive`,
`config`, `certificates`, `translations`) or to the step command, and each program parses its arguments with its own
`argparse` parser. The step command builds one subparser per registered step from the step's `Argument`s, after a
first pass that reads `--root` to know which packs the workspace selects.

## Goals / Non-Goals

**Goals:**

- One command-line library, and no dispatcher of Veriphy's own.
- The same commands, outputs and exit statuses.

**Non-Goals:**

- New commands, or renamed options.

## Decisions

### D1. One group, assembled from the layers

`veriphy.__main__` defines the `veriphy` group and adds each layer's and pack's commands to it. A layer's module
exposes a click command or group (`claims`, `agents`, `primitive`, `config`, `records`), and a pack's catalog the same
(`certificates`, `translations`). The group is the console script, and `python -m veriphy` runs it.

### D2. Steps become commands lazily

The step commands depend on the workspace's packs, so the group is a `click.Group` whose `list_commands` and
`get_command` read the registered steps of the workspace named by `--root` (or found from the working directory).
Each step's `Argument`s map to `click.argument` and `click.option`, with the same names, types and defaults.

### D3. Exit statuses through click

A command signals its status with `ctx.exit(code)`, keeping 0 for accepted, 1 for refused, a counterexample or a
failure, 2 for bad usage (click's own) and 3 for unchecked or undecided.

## Risks / Trade-offs

- [Help text and error wording change slightly] → Click's wording replaces argparse's; tests assert on statuses and
  outputs, not on the parsers' phrasing.
