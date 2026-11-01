# Proposal

## Why

Veriphy checks one claim at a time. Research errors in physics often sit between claims: a lemma proved under one
normalization and used under another, a theorem proved in Lean that rests on a claim Sage only tested, a convention
change whose consequences nobody traced. Open Ontologies (`fabio-rovai/open-ontologies`, MIT) reasons over RDF graphs
and writes derivation certificates that a separate Lean checker, `oo-horn`, accepts or refuses. Its pure-Python engine
`open-ontologies-lite` makes it usable from Veriphy without a Rust toolchain. With it, Veriphy can give the structure
of a whole paper or research program the same treatment it gives a single claim: an untrusted engine computes, and a
verified checker decides.

## What Changes

- A research claim graph per project under `.veriphy/graph/`: claims, conventions, concepts and sources as RDF, in
  a vocabulary Veriphy ships, with the provenance of every assertion (`lean`, `agent` or `human`).
- A Lean command `#veriphy_graph` that exports the project's formalized claims, their verification levels and their
  dependencies as the kernel sees them, so these facts come from Lean and not from extraction.
- Certified reasoning over the graph: Veriphy states the meaning of its vocabulary as OWL axioms on the checker's
  built-in rules, `open-ontologies-lite` derives the consequences and writes a certificate, and `oo-horn` checks it.
  Veriphy reports only the verdict the checker printed, `entailed` for an accepted run, and reports an unchecked
  result as unchecked.
- Convention impact: for a convention, every claim that assumes it directly or through its dependencies. For an edit
  to the graph, a plan that lists the consequences it adds and removes before the edit is kept.
- Effective levels: each claim's own level and a certified cap from what it rests on, so a theorem that depends on an
  `oracle-test` claim is reported at most `oracle-test`. Reasoning only ever lowers a level.
- Graph checks: SHACL shapes on claims (reported as a measurement, not a proof), and certified clash detection for a
  claim or concept that assumes two conventions which exclude each other, within a paper or across papers.
- Context slices: for a claim, the statements, conventions and definitions its certified consequences rest on, as
  context for the proving agent, with a check that the slice keeps every consequence about the claim.
- A research workflow in the plugin: extract claims from a draft into the graph, triage them, prove with slices,
  export the results, and produce a verification appendix per source in Markdown and LaTeX.
- A command that builds `oo-horn` and installs the `open-ontologies-lite` reasoner from one pinned Open Ontologies
  release, and an optional extra `veriphy[graph]` with the reasoner's dependencies.

## Capabilities

### New Capabilities

- `research/claim-graph`: the vocabulary, the files under `.veriphy/graph/`, node identity, provenance, and links
  between sources and across papers.
- `research/lean-claim-export`: the `#veriphy_graph` command and the facts it exports from the Lean environment.
- `research/certified-graph-reasoning`: the vocabulary axioms, running the reasoner, certificates, the `oo-horn`
  check, verdict reporting, and building the checker.
- `research/convention-impact`: the claims affected by a convention, and plans for an edit to the graph.
- `research/effective-levels`: own levels, certified level caps along dependencies, and the level report.
- `research/graph-checks`: SHACL shapes on the graph and certified convention clashes.
- `research/context-slices`: slices of the graph for one claim and the check that a slice keeps its consequences.
- `research/research-workflow`: the plugin skill and recipes for claim extraction, triage, proving with slices and
  the verification appendix.

### Modified Capabilities

- `certificates/project-layout`: `.veriphy/graph/` joins the layout of Veriphy artifacts.

## Impact

- New package `veriphy.graph` (no Sage import) with a Python API and the CLI `python -m veriphy.graph`.
- New optional extra `graph` in `pyproject.toml` with `pyoxigraph` and `pyshacl`. The reasoner itself comes from the
  pinned release through the checker build, because its PyPI release lacks the Horn reasoner. The default install is
  unchanged.
- New Lean module `Veriphy/Kit/Graph.lean` with `#veriphy_graph`, imported by `Veriphy.lean`.
- New plugin skill `research`, recipes and prompts. The `prove` skill gains an optional step that loads a slice.
- `oo-horn` is an external binary built from Open Ontologies at a pinned tag with its own Lean toolchain. Veriphy
  neither vendors nor links it.
- CI: the integration job builds `oo-horn` at the pinned tag and runs the graph tests against it.
- Documentation: a user-guide section, a components row, the changelog, and the Project Profile in the constitution.
