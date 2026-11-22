# Proposal

## Why

A pack is meant to bring a field to Veriphy, but the shipped packs mixed three things: the framework itself (`core`),
a tool (`lean`) and a method (`reproduction`), with only `math` a field. The reproduction pack also needed R and a
container runtime, a second language and a second installation for its users. Skills, examples, Lean sources and
maintenance scripts sat outside the packs they belong to.

## What Changes

- **BREAKING** The framework's own entries (records, the claim graph, the agent steps, `validate`, `reason`,
  `appendix`, the level `none`) are a framework pack every workspace has and none chooses: `core` is no longer named.
- **BREAKING** The `lean` pack is part of `math`: its primitives, steps, scopes and level move there, and the Lean
  library with its Lake files (`lakefile.toml`, `lean-toolchain`, `lake-manifest.json`) moves to
  `src/veriphy/packs/math/lean/`. A Lean project requires Veriphy with `subDir = "src/veriphy/packs/math/lean"`.
- **BREAKING** The `reproduction` pack is replaced by `social-science`: the authors' analysis runs as a Python script
  in a fresh process (no R, no container), and a new step, `check-concepts`, checks every construct a claim uses
  against a SKOS thesaurus, such as ELSST. The pack adds the `sampling` convention; how a construct is measured is a
  convention, so two measures of one construct clash in the claim graph.
- Skills live in their packs' agents layer (`packs/<pack>/agents/skills/`), named in the plugin manifest.
- Examples live in `docs/examples/`: a social-science study and two example packs, `economics` and `history`, which
  the test suite runs.
- The `scripts/` directory goes: rendering the diagrams, regenerating the translation tables and bundling
  `VeriphyCheck` are the nox sessions `diagrams`, `tables` and `bundle`.
- A tool's command may name `{pack}`, its pack's directory, and a local pack's Python imports from its directory.
- A pack's name may hold a dash; its package then holds an underscore.

## Capabilities

### New Capabilities

- `packs/social-science`: the social-science pack.

### Modified Capabilities

- `packs/reproduction`: removed, replaced by `packs/social-science`.
- `core/workspace-config`: the framework pack, and local packs' code.
- `core/primitives`: the shipped packs.
- `distribution/releases`: the Lean library in the math pack.

## Impact

- `src/veriphy/packs/` (`core`, `math`, `social_science`), the Lean library and its Lake files, `noxfile.py`, CI,
  the plugin manifest, the docs and the tests.
- Dependents' lakefiles add `subDir`.
