# Proposal

## Why

Using the research claim graph takes two commands today: `sage -pip install 'veriphy[graph]'`, then
`sage -python -m veriphy.graph checker build`. A user who runs only the first gets `unchecked` results or a missing
reasoner. pip cannot do the second step, because PyPI refuses git dependencies and a wheel runs nothing at install
time. So the second step should happen by itself the first time a graph command needs it. The README does not mention
the graph at all since 0.4.0, so a reader cannot find out how to install or use it.

## What Changes

- The first graph command that needs the reasoner or the checker sets them up from the pinned Open Ontologies release
  and says what it does. Later commands reuse the cache. `sage -pip install 'veriphy[graph]'` becomes the only
  installation command.
- The reasoner is imported from the cached release source, not installed with pip at run time, so nothing is written
  into the Python environment after installation. **BREAKING** for nobody in practice: `checker build` no longer
  installs `open-ontologies-lite` into the interpreter.
- On Linux x86_64 the checker is the release's prebuilt `oo-horn`, verified against a SHA-256 that Veriphy pins and
  against the release's `SHASUMS.txt`. Elsewhere it is built from the release, as today. `checker build` uses the
  same path, so it is fast on Linux.
- The fetched release is checked against the commit Veriphy pins, so a moved tag is refused.
- `VERIPHY_OO_HORN` still names a checker. A new variable, `VERIPHY_GRAPH_SETUP=off`, turns automatic setup off for CI
  and offline machines, and the results are then `unchecked` with the command that sets them up.
- The README covers the research claim graph: what it is, the single install command, the main commands, and the
  `research` skill.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `research/certified-graph-reasoning`: the checker and the reasoner are set up on first use, the prebuilt checker is
  used where the release ships one, the release commit is pinned, and automatic setup can be turned off. The
  `research/research-workflow` spec already asks only for the extra, so only its documents change.

## Impact

- `veriphy.graph._checker` (setup on first use, download and verification, pinned commit and hash),
  `veriphy.graph._engine` (the reasoner imported from the cache), `veriphy.graph._reasoning` (setup before a run).
- Tests with a local fake release (no network). The CI integration job's build step downloads the checker, and its
  fixture-chapter workflow runs from an empty cache to exercise first-use setup.
- README, user guide, `prompts/research.md` and the `research` skill: one install command.
- No new dependency. The download uses the standard library.
