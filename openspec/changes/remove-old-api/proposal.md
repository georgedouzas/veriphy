# Proposal

## Why

The layered architecture kept every old name working, with a deprecation warning, for one minor release. Before it
merges, the old names go: two spellings of each operation double what users and agents must learn and what the tests
must cover, and several new forms are still macros over the old ones, so the old code paths remain the real ones.

## What Changes

- **BREAKING** The alias packages `veriphy.toolkit`, `veriphy.graph`, `veriphy.oracle`, `veriphy.prompts`,
  `veriphy.sage_server`, `veriphy.certificates` and `veriphy.translations` are removed, with their programs
  (`python -m veriphy.graph` and the others). Scripts import `veriphy.script`; the commands are `veriphy layers <layer>` and `veriphy pack math <program>`.
- **BREAKING** The Lean tactics `sage_run` and `sage_test` and the commands `#veriphy_meaning`,
  `#veriphy_check_translations`, `#veriphy_coverage`, `#veriphy_translate`, `#veriphy_graph`, `#veriphy_tables` and
  `#veriphy_levels` are removed. `veriphy certify`, `#veriphy test`, `#veriphy meaning` and the other `#veriphy <verb>`
  forms elaborate directly, and `warnDeprecated` goes.
- **BREAKING** The verb `elaborate` is removed; `check` is the verb.
- **BREAKING** A script that assigns `proof` (or the other result variables) instead of returning from
  `run(goal, inputs)` is refused, saying how to return.
- **BREAKING** The Sage session answers JSON-RPC 2.0 requests only; a request without `"jsonrpc": "2.0"` gets a
  JSON-RPC parse error.
- **BREAKING** The per-group entry points go: `python -m veriphy.claims`, `veriphy.agents`,
  `veriphy.packs.math.steps.certificates` and `veriphy.packs.math.primitives.translations`, and the `main()` of each
  group. `veriphy` (or `python -m veriphy`) is the one command.
- **BREAKING** Veriphy keeps no process alive between calls. Sage's methods run once per call as a `files` tool
  (`sage -python -m veriphy.packs.math.primitives.sage call <method> <input> <out>`), so the `jsonrpc` contract, its
  session client and the `method` fields go. Lean runs `lake env lean` once per call, so the Lean REPL, its build and
  its cache go. Only Lean keeps a Sage session, while it compiles a file.
- **BREAKING** The `veriphy-sage-server` console script goes; Lean starts the session with
  `sage -python -m veriphy.packs.math.primitives.sage`, as before.
- **BREAKING** The catalog no longer reads the 0.1.0 top-level `certificates/` directory; scripts live in
  `.veriphy/certificates/`.
- **BREAKING** The Sage process Lean talks to is called what it is, the Sage session: no longer "daemon" or
  "server". `VERIPHY_SAGE_SERVER` is now `VERIPHY_SAGE_SESSION`, the module `sage._server` is `sage._session`, and the
  specs `distribution/daemon-package`, `distribution/daemon-resolution` and `certificates/daemon-session` are
  `distribution/sage-package`, `distribution/sage-resolution` and `certificates/sage-session`.
- `veriphy.core._aliases` keeps only `reexport`, which the `veriphy.script` facade uses.
- The docs, specs, skills, saved certificates and tests use only the current names.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `certificates/project-layout`: the 0.1.0 layout is no longer read.
- `distribution/sage-package`: one entry point for the Sage session.
- `core/primitives`: one contract, `files`, and one process per call.
- `core/operations`: the deprecated forms are removed.
- `core/module-layout`: the deprecated aliases are removed.

## Impact

- Python: the seven alias packages, `veriphy.core._aliases`, `veriphy.steps` (`DEPRECATED_VERBS`), the Sage session's
  protocol and script reading.
- Lean: `Veriphy/Kit/Deprecation.lean`, the old syntaxes in `Tactic` and `Kit`, `VeriphyTest/Deprecated.lean`.
- Projects with saved scripts or proofs using the old names must move to the new ones; the release notes list each.
