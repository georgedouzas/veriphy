# Spec Delta

## Purpose

Defines how the Lean bridge finds and starts the Sage daemon: a default that works for a released install with no configuration, the overrides for custom Sage locations and development, and the errors when it cannot start.

## ADDED Requirements

### Requirement: Default daemon command
With no overrides set, the bridge SHALL start the daemon as `sage -python -m veriphy.sage_server`, resolving `sage` on `PATH`. It SHALL need no repository path, working directory or environment variable.

#### Scenario: Proving outside the Veriphy repo
- **WHEN** a Lake project that requires Veriphy runs `sage_lincomb`, with Sage on `PATH`, `veriphy` installed in Sage, and no Veriphy environment variables
- **THEN** the tactic reaches the daemon and closes the goal

### Requirement: Sage executable override
`VERIPHY_SAGE_CMD`, when set, SHALL replace `sage` as the executable the bridge runs, with the same `-python -m veriphy.sage_server` arguments.

#### Scenario: Sage not on PATH
- **WHEN** `VERIPHY_SAGE_CMD=/opt/sage/sage` is set and `sage` is not on `PATH`
- **THEN** the bridge starts `/opt/sage/sage -python -m veriphy.sage_server`

### Requirement: Development script override
`VERIPHY_SAGE_SERVER`, when set, SHALL make the bridge run that script file with `<sage> -python <script>` instead of the installed module. A path that does not exist SHALL be an error naming the variable and the path.

#### Scenario: Working on the daemon in a checkout
- **WHEN** `VERIPHY_SAGE_SERVER=src/veriphy/sage_server.py` is set in the repo
- **THEN** tactics use that file, so daemon edits take effect without reinstalling

#### Scenario: Stale development path
- **WHEN** `VERIPHY_SAGE_SERVER` points at the removed `sage_bridge/server.py`
- **THEN** the tactic fails with an error naming `VERIPHY_SAGE_SERVER` and the missing path

### Requirement: Actionable start-up failures
If the daemon process cannot be started, or exits before answering, the tactic SHALL fail with a message that states the cause and the fix. It SHALL NOT report a JSON parse error. The message SHALL include the start-up stderr, truncated.

#### Scenario: Package not installed in Sage
- **WHEN** Sage is on `PATH` but `veriphy` is not installed in it
- **THEN** the error says the daemon module is missing and to run `sage -pip install veriphy` (matching the Lean library's version)

#### Scenario: Sage missing
- **WHEN** neither `sage` on `PATH` nor `VERIPHY_SAGE_CMD` resolves to an executable
- **THEN** the error says Sage could not be started, and names `VERIPHY_SAGE_CMD`

### Requirement: Version agreement warning
When the daemon's reported `veriphy` version differs from the Lean library's version, the bridge SHALL still proceed and SHALL log a warning that names both versions, at most once per Lean process.

#### Scenario: Mismatched install
- **WHEN** Lean Veriphy `0.4.0` talks to a daemon reporting `0.3.9`
- **THEN** the tactic runs normally and a warning names both versions

### Requirement: Committed proofs stay Sage-free
Resolution changes SHALL NOT affect proofs that use only emitted replacements. They SHALL elaborate with no Sage and no `veriphy` Python package present.

#### Scenario: Downstream CI without Sage
- **WHEN** a project containing only committed `Try this:` replacements builds on a machine without Sage
- **THEN** the build succeeds and no daemon start is attempted
