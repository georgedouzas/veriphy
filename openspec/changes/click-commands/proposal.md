# Proposal

## Why

The `veriphy` command is eight hand-written `argparse` programs (the steps, `claims`, `agents`, `primitive`, `config`,
`certificates`, `translations`) and a dispatcher of Veriphy's own in `veriphy.__main__` that routes the first argument
to one of them. Click already does what the dispatcher and the parsers do (nested command groups, generated help,
typed options, exit codes, a test runner), so Veriphy should use it instead of keeping its own.

## What Changes

- `veriphy` is one click group. Each layer and pack contributes its commands to it: the steps add one command per
  registered step, and `claims`, `agents`, `primitive`, `config`, `certificates`, `translations` and `records` are
  subgroups or commands.
- A step's `Argument`s become click arguments and options, so `veriphy <verb> --help` is generated from the step.
- `veriphy.__main__`'s dispatcher and every `argparse` parser go; `python -m veriphy …` runs the same click group.
- Behaviour, outputs and exit statuses stay as they are; the old `python -m veriphy.<module>` programs run the same
  click commands.

Depends on `packs-and-config`.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `core/operations`: the shell command is one click group, its subcommands contributed by the layers and packs.

## Impact

- `pyproject.toml`: `click`.
- Every command module: `veriphy.__main__`, `veriphy.steps._cli`, `veriphy.claims._cli`, `veriphy.agents._cli`,
  `veriphy.primitives._cli`, `veriphy.core._config`, the certificate and translation catalogs.
- Tests: click's `CliRunner` where a test called a `main(argv)`.
