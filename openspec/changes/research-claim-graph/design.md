# Design

## Context

See proposal.md for the motivation and the specs under `specs/research/` for the requirements. The constraints that
shape the approach:

- Veriphy's Python runs inside Sage (`sage -pip install veriphy`), but `veriphy` and `veriphy.core` must not import
  Sage. The graph work needs no Sage at all.
- The Lean library is pinned to `leanprover/lean4:v4.34.1` and builds against mathlib. The Open Ontologies checkers
  are core Lean on `v4.33.1`, with no mathlib.
- Open Ontologies ships three engines: the Rust binary (`open-ontologies`, with plan, SHACL checked in Lean, and MCP),
  the pure-Python `open-ontologies-lite` (Horn reasoner, certificate emitter, SHACL through `pyshacl`), and the Lean
  checkers (`oo-cert`, `oo-horn`, and others). `open-ontologies-lite` depends on `pyoxigraph<0.6` and nothing else in
  its base install.
- The PyPI release `open-ontologies-lite` 0.5.0 (21 August 2026) has no Horn reasoner. `run_horn` and `check_horn`
  exist only in the repository source, at tag `v2.1.0` under the same version string. PyPI refuses a package whose
  dependencies are git URLs, so Veriphy cannot declare the tagged source as a dependency.
- `oo-horn` decides between `entailed` and `entailed_under_supplied_rules` by comparing the run's rule table with its
  built-in table byte for byte. Its built-in table holds `rdfs2`–`rdfs11`, `prp-trp`, `prp-symp`, `prp-inv1/2`,
  `eq-sym`, `scm-*`, `cls-svf1`, `cls-avf` and `cls-hv1/2`. It has no `eq-rep`, no `cls-int` and no `prp-spo2`.
- Levels already exist in Lean (`levelOf`, `#veriphy_levels` in `Veriphy/Kit/Levels.lean`), and test records live in
  `.veriphy/tests/`.

## Goals / Non-Goals

**Goals:**

- Every graph conclusion Veriphy reports is either accepted by `oo-horn`, with the verdict it printed, or labelled
  `unchecked`.
- The facts about formalized claims (levels, dependencies) come from the Lean environment.
- The graph works without Sage, and the default install of `veriphy` is unchanged.

**Non-Goals:**

- The Rust binary, its MCP server, its `plan` command, and its Lean-checked SHACL. Veriphy's own plan compares two
  checked runs, and SHACL stays a measurement.
- Rules a user writes. Every run uses the built-in table, so every accepted run earns `entailed`.
- Certifying that a prose claim and its Lean statement say the same thing. `formalizedBy` is an assertion with a
  provenance, and the reports show it.
- Certifying the absence of a consequence, such as "no clash". Horn certificates prove what is derived, not what is
  not.

## Decisions

### D1. `open-ontologies-lite` as the engine, `oo-horn` as the checker

Veriphy uses `run_horn` from `open-ontologies-lite` to derive and write certificates, and its `check_horn` to call
`oo-horn` with an explicit path. Alternatives:

- The Rust binary: more features, but a second binary to install per platform and no Python API. The features
  Veriphy needs (Horn reasoning and certificates) are in the lite package.
- The MCP server: serves the agent only. The constitution asks for parity between delivery surfaces, and a CLI plus a
  Python API serve the agent, CI and a reviewer alike.
- A reasoner inside Veriphy: duplicates a working engine and gains nothing, since the warrant is in the checker.

### D2. The vocabulary's meaning as generated OWL axioms, not supplied rules

Supplied rules would earn only `entailed_under_supplied_rules`, and Veriphy's rules would become assumptions of every
conclusion. Instead, `veriphy.graph` generates, for each convention and each level in the graph, OWL restriction
classes that the built-in rules evaluate. For a convention `k`:

```
A_k   ≡ hasValue restriction   (onProperty vp:assumes,     hasValue k)        cls-hv1, cls-hv2
U_k   = someValuesFrom          (onProperty vp:uses,        someValuesFrom A_k) cls-svf1
S_k   = someValuesFrom          (onProperty owl:sameAs,     someValuesFrom A_k) cls-svf1
U_k ⊑ A_k,  S_k ⊑ A_k                                                          rdfs9
vp:realizes owl:inverseOf vp:realizedBy,  vp:realizes ⊑ vp:assumes            prp-inv1, rdfs7
```

`a uses b` and `b assumes k` give `a ∈ U_k` (`cls-svf1`), then `a ∈ A_k` (`rdfs9`), then `a assumes k` (`cls-hv1`).
For a level `L`, the same pattern on `vp:cappedAt` (with `vp:hasLevel ⊑ vp:cappedAt`) and on both `vp:uses` and
`vp:formalizedBy` gives caps that follow dependencies and formalizations, and `Cap_L ⊑ Cap_M` for `L` below `M` gives
caps at every higher level. `owl:sameAs` is symmetric through `eq-sym`. The generated classes have IRIs, not blank
nodes, under `urn:veriphy:axiom:`, so every certificate line is readable.

A clash needs a conjunction, which the built-in table cannot derive. A clash is therefore reported as two checked
`assumes` conclusions and one asserted `excludes` triple, joined in Python. Every part is checked or asserted, and no
rule is assumed.

A claim with no level and no formalization gets a generated `vp:hasLevel vp:none` (provenance `veriphy`) before the
run, because Horn reasoning cannot derive from an absence. This only lowers caps, so the generation is safe.

### D3. Provenance by file, not by reification

Each source has one Turtle file per provenance: `<source>.agent.ttl`, `<source>.human.ttl`. The Lean export writes
N-Triples under `.veriphy/graph/lean/`, and generated axioms are never written to the project, only to the run's
certificate. Confirming a triple moves it from the agent file to the human file. Alternatives: RDF-star annotations
(the lite reasoner skips quoted triples) and TriG named graphs (less familiar, worse diffs). Files keep each
provenance reviewable in git.

### D4. Node IRIs

Source nodes are `urn:veriphy:source:<source>#<label>`, with `<source>` the file stem, an arXiv identifier
(`arXiv:0808.3236`) or a DOI. Lean nodes are `urn:veriphy:lean:<Lean name>`. The vocabulary is
`urn:veriphy:vocabulary#`. URNs avoid claiming a web domain and are stable across machines.

### D5. Lean export in `Veriphy/Kit/Graph.lean`

`#veriphy_graph p₁ … pₙ` walks the environment's constants under the prefixes. It reuses `levelOf` for levels and
`ConstantInfo.getUsedConstants` on type and value for `uses`, filtered to the exported set. It writes
`.veriphy/graph/lean/export.nt` with each claim's type, pretty-printed, as its `statement`. It resolves `.veriphy/` the
way `sage_test` does for its records. N-Triples is chosen because it is one triple per line, so the Lean side needs no
Turtle writer.

### D6. Package `veriphy.graph`

A new package that never imports Sage:

- `_vocabulary.py`: loads the shipped `vocabulary.ttl` and `shapes.ttl`, and generates the axioms of D2.
- `_store.py`: loads the project's files with their provenance, and resolves the root through `veriphy.core`.
- `_checker.py`: finds `oo-horn` (environment variable `VERIPHY_OO_HORN`, then the cache) and builds it.
- `_reasoning.py`: runs `run_horn`, writes the run directory, calls `check_horn`, and returns a typed run result.
- `_levels.py`, `_impact.py`, `_slices.py`, `_shapes.py`, `_appendix.py`: the capabilities, each over a run result.
- `__main__.py`: the CLI `python -m veriphy.graph` with the subcommands `validate`, `reason`, `recheck`, `levels`,
  `impact`, `plan`, `slice`, `excludes`, `confirm`, `appendix`, `axioms`, `vocabulary` and `checker`.

`open-ontologies-lite` is imported in one module, behind the one allowed lazy import. A missing reasoner raises
`GraphExtraMissing` from `veriphy.core`, with the two install lines: `sage -pip install 'veriphy[graph]'` and
`sage -python -m veriphy.graph checker build`. The CLI and the
Python API expose the same capabilities, and a parity test asserts it.

### D7. Building `oo-horn` and installing the reasoner from one tag

`python -m veriphy.graph checker build` clones Open Ontologies at the pinned tag (`v2.1.0`) into
`$XDG_CACHE_HOME/veriphy/open-ontologies/<tag>` (default `~/.cache/...`), runs `lake build oo-horn` in its `lean/`
directory, and installs the clone's `python/` package into the running interpreter with `pip`. `elan` installs the
`lean/` directory's own toolchain. The `graph` extra declares `pyoxigraph` and `pyshacl`, the reasoner's own
dependencies, and not `open-ontologies-lite`, whose PyPI release lacks the reasoner. Reasoner and checker therefore
always come from the same tag. When upstream publishes a release with the reasoner, the extra pins it and the build
command stops installing it. The alternatives were a reasoner written in Veriphy (a third copy of an engine upstream
maintains twice) and waiting for an upstream release. Veriphy does not vendor or link the checker. A different
toolchain is what keeps the checker independent of Veriphy, which is the point of the second check. A test compares
the built-in table that `open-ontologies-lite` writes with what `oo-horn rules` prints, and fails on drift.

### D8. Plans against a git revision

`plan --against REV` reads each graph file at `REV` with `git show`, reasons over both graphs, has both runs checked,
and diffs the checked conclusions about `assumes`, caps and clashes. Only checked conclusions enter the diff.

### D9. Slices from certificate premises

The slice of a claim is the closure of premises, through earlier derivation lines, of every derivation whose
conclusion has the claim as subject, plus the claim's own assertions. Veriphy then reasons over the slice alone, has it
checked, and compares the conclusions about the claim. The comparison, not the construction, is what lets Veriphy
offer the slice.

### D10. The research skill

`skills/research/SKILL.md` (mirrored into `.claude/skills/research/`) and `prompts/research.md` describe the loop:

1. Extract claims to `<source>.agent.ttl`.
2. Validate against the shapes.
3. Triage, with the numerical check from `prove`.
4. Formalize with the slice as context.
5. Prove with `prove`/`certify`.
6. Link with `formalizedBy`.
7. Run `#veriphy_graph`.
8. Reason, then write the levels report and the appendix.

`prove` gets one optional step: when the claim has a graph node, load its slice first. Triage groups are recorded with
`vp:triage` in the agent file.

## Risks / Trade-offs

- [Extraction errors: an agent tags a claim with the wrong convention, and a checked conclusion is faithfully wrong]
  → Provenance counts in every report, the `confirm` command, and Lean-sourced facts wherever a claim is formalized.
- [Open Ontologies moves fast: the reasoner or the certificate format changes] → Reasoner and checker come from one
  pinned tag, installed by one command. The drift test fails rather than skips.
- [The reasoner is installed outside pip's resolution, by `checker build`] → The command prints what it installed and
  from which commit. `GraphExtraMissing` names the command when the reasoner is absent, and the CI job runs the same
  command. Veriphy relies only on the Horn certificate format,
  which Open Ontologies' decision 0003 fixes.
- [Building `oo-horn` needs `elan`, `git` and minutes of build time] → The build is cached per tag, the explicit path
  overrides it, and without a checker every result is labelled `unchecked` instead of failing.
- [The axiom encoding is indirect and could encode the wrong meaning] → One test per propagation path, such as `uses`
  chains, `realizedBy`, `sameAs`, `formalizedBy` and the level order, each checked by the real checker in CI.
- [A graph of thousands of claims produces many generated classes] → Two to four classes per convention and level,
  which is linear in the number of conventions. `pyoxigraph` handles graphs far larger than a book.
- [The default install must not change] → The dependency lives in the `graph` extra, and `veriphy.graph` is not
  imported by `veriphy`.

## Migration Plan

No migration. Existing projects keep working. A project opts in by installing the extra, building the checker, and
creating `.veriphy/graph/sources/`. Rollback is uninstalling the extra and deleting `.veriphy/graph/`.

## Open Questions

- Whether to add the Rust binary's Lean-checked SHACL later, so the shapes report can become a checked result. This
  adds an engine but changes none of the specs above.
