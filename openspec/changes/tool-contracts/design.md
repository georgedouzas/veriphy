# Design

## Context

`_checker.py` pins `oo-horn` by commit and SHA-256 and sets it up on first use. The Lean bridge starts
`sage -python -m veriphy.sage_server` and reads `VERIPHY_SAGE_CMD`, `VERIPHY_SAGE_SERVER` and `VERIPHY_SAGE_TIMEOUT`.
The daemon protocol is JSON lines, and the toolkit is imported by 32 files as `veriphy.toolkit`.

## Goals / Non-Goals

**Goals:**

- Any tool runs from YAML alone, and runs only at its pinned version.
- SageMath and `oo-horn` behave as today from the user's point of view.

**Non-Goals:**

- Moving the toolkit's code. It is the `math` pack's library where it is.
- A container runtime for Sage. Sage stays the user's installation, pinned by version.

## Decisions

### D1. Two contracts cover every tool we know

A batch tool (R, Stata, a solver) fits **files**, and a session tool (Sage, a REPL) fits **json-lines**. Both receive
inputs as files or JSON, never as shell-interpolated text, so a value cannot inject a command.

### D2. Three kinds of pin

`image: name@sha256:…` runs the tool in a container with that digest. `commit` plus `sha256` fetches and verifies a
release, as `oo-horn` does today. `version` runs the installed tool and compares its reported version. The first two
are exact, the third trusts the tool's report, and the record says which kind was used.

### D3. Seeds go through the contract

A tool with `seed:` receives the step's seed through the declared placeholder. A random tool without `seed:` is
refused by `config check`.

### D4. Lean asks the config, environment wins

The bridge runs `python -m veriphy config show --tool sage --json` once per Lean process when it can, and falls back
to today's defaults. The environment variables keep overriding, so existing setups keep working.

## Risks / Trade-offs

- [Version pins trust the tool's own report] → The record names the pin kind, and packs prefer image or hash pins.
- [A container runtime for image pins] → Only tools pinned by image need one, and `config check` says so.
