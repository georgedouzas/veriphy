# Tasks

Every `lake build` and `lake env lean` runs one Lean process at a time.

## 1. Setup

- [x] 1.1 Add the optional extra `graph = ["pyoxigraph>=0.5,<0.6", "pyshacl>=0.26"]` to `pyproject.toml`, configure `deptry` for `open_ontologies_lite` (installed by `checker build`, D7), and install the extra in the `tests` nox session. Verify that `uv sync` and `nox -s checks` pass, and that `pip install veriphy` without the extra installs no new package.
- [x] 1.2 Create the package `veriphy.graph` with its `__init__`, `__all__` and `__main__`, and add `GraphError`, `GraphExtraMissingError` and `CheckerError` to `veriphy.core` (D6). Verify that `python -c "import veriphy"` does not import `open_ontologies_lite` and that `python -m veriphy.graph --help` runs.

## 2. Vocabulary and project graph (claim-graph, project-layout)

- [x] 2.1 Write `vocabulary.ttl` (classes, properties, the four levels and their order) and ship it as package data (D4). Verify with pytest that it parses, declares every term the spec lists, and states `none` below `oracle-test` below `kernel-test` below `certificate`.
- [x] 2.2 Load a project graph from `.veriphy/graph/sources/<source>.<provenance>.ttl` and `.veriphy/graph/lean/`, with root resolution through `veriphy.core` (D3). Verify with pytest on fixture projects: a multi-file load with counts per file, a syntax error with file and line, a file without a provenance, and an undeclared property in the Veriphy namespace.
- [x] 2.3 Build node IRIs for source and Lean nodes and resolve links across sources, including arXiv and DOI sources (D4). Verify with pytest for same labels in two sources, a cross-source `uses`, and a stable Lean IRI.
- [x] 2.4 Add the `confirm` and `vocabulary` CLI commands. Verify with pytest that confirming moves exactly one triple from the agent file to the human file.
- [x] 2.5 Document `.veriphy/graph/` in the user guide's layout section, and update the layout list in `docs/` to include `.veriphy/tests/` and `.veriphy/graph/`. Verify with `nox -s docs`.

## 3. Lean export (lean-claim-export)

- [x] 3.1 Add `Veriphy/Kit/Graph.lean` with `#veriphy_graph p₁ … pₙ`: claims and definitions with levels from `levelOf`, `uses` from the used constants of type and value filtered to the exported set, and statements, written to `.veriphy/graph/lean/<prefixes>.nt` (D5). Import it from `Veriphy/Kit.lean`. Verify with `VeriphyTest` tests on a module with a certified, a tested, a plain theorem and a definition: the written triples, the counts message, and the error for an unknown prefix.
- [ ] 3.2 Load the export in `veriphy.graph` with provenance `lean`. Verify with pytest on a recorded `export.nt`, and in the integration job by exporting `VeriphyTest` and loading it.
- [x] 3.3 Document `#veriphy_graph` in the user guide. Verify with `nox -s docs`.

## 4. Certified reasoning (certified-graph-reasoning)

- [x] 4.1 Generate the vocabulary axioms for the conventions and levels of a graph: hasValue and someValuesFrom classes for `uses`, `owl:sameAs`, `formalizedBy`, `realizedBy`, the level order, and `hasLevel none` for claims with no level (D2). Add the `axioms` CLI command. Verify with pytest that the generated triples use only IRIs under `urn:veriphy:axiom:` and that their number is linear in conventions and levels.
- [ ] 4.2 Find and build `oo-horn`, and install the reasoner from the same clone: `VERIPHY_OO_HORN`, then the cache, and `checker build` at the pinned tag (D7). Verify with pytest using a fake `git`, `lake` and `pip` on `PATH` for the commands run and the cache path, and in the integration job by a real build.
- [ ] 4.3 Run reasoning: `run_horn` with the built-in table, the run directory under `.veriphy/graph/runs/<run>/` with the digest, the `check_horn` call, and a typed result with status, verdict and theorem copied from the checker. Unchecked, incomplete and rejected runs are labelled so (D1). Add the `reason` and `recheck` commands. Verify with pytest using a fake checker for each status, and with the real checker in the integration job on: a transitive `assumes`, `realizedBy`, `owl:sameAs`, `formalizedBy`, a level chain, and a forged derivation line that is rejected.
- [ ] 4.4 Add the drift test that compares the built-in table bytes of `open-ontologies-lite` with `oo-horn rules`, failing rather than skipping when the checker is present. Verify that it runs in the integration job.
- [ ] 4.5 Run the integration job with the checker: cache the built `oo-horn` per tag and set `VERIPHY_OO_HORN` for the graph tests. Verify with a green CI run.
- [x] 4.6 Document the reasoning, the verdict words, and the checker build in the user guide and the components page. Verify with `nox -s docs`.

## 5. Effective levels (effective-levels)

- [x] 5.1 Compute own levels (export, `formalizedBy`, or `none`) and effective levels from the checked caps, with the capping claim. Add the `levels` command with the per-source report and the summary. Verify with pytest for: a prose claim with a formalization, a prose claim alone, a theorem on an `oracle-test` lemma, a dependency without a level, and an unchecked run.
- [x] 5.2 Add a property test that no generated axiom derives a cap above a claim's own level, on random graphs. Verify with pytest.

## 6. Convention impact (convention-impact)

- [x] 6.1 Add `impact <convention>`: the affected claims by source, each with its `uses` chain and its Lean name and level. Verify with pytest for direct and transitive claims, a formalized claim, and an unchecked run.
- [x] 6.2 Add `plan --against REV` over two checked runs, diffing `assumes`, caps and clashes (D8). Verify with pytest on a temporary git repository: switching a convention, and an edit that changes only a statement.
- [x] 6.3 Document impact and plans with a worked example in the user guide. Verify with `nox -s docs`.

## 7. Graph checks (graph-checks)

- [x] 7.1 Write `shapes.ttl` and validate the graph with it, labelling the report as a SHACL measurement. Verify with pytest for a claim without a statement, a broken `formalizedBy` link, a broken `realizedBy` link, and a conforming graph.
- [x] 7.2 Add `excludes`: propose `excludes` triples for conventions that share `conventionFor`, written on confirmation. Verify with pytest for two metric signatures.
- [x] 7.3 Report clashes as two checked `assumes` conclusions joined with an asserted `excludes` triple, including inherited and cross-source assumptions (D2). Verify with pytest and with the real checker on the cross-paper scenario, and check that the no-clash report says it is not a checked conclusion.
- [x] 7.4 Document shapes and clashes in the user guide. Verify with `nox -s docs`.

## 8. Context slices (context-slices)

- [x] 8.1 Compute a claim's slice from the certificate's premises, reason over it, have it checked, and compare the consequences about the claim (D9). Verify with pytest for a complete slice and for a slice with a removed premise that is reported as lost and not offered.
- [x] 8.2 Render a slice as Markdown for the agent, and add the `slice` command. Verify with pytest that the rendering names statements, conventions with their aspects, Lean names and effective levels.

## 9. Research workflow (research-workflow)

- [x] 9.1 Add the `appendix` command, writing Markdown and LaTeX with the level columns, provenance counts, verdict and recheck commands, and the unchecked wording. Verify with pytest snapshots of both formats for a checked and an unchecked run, and that the LaTeX compiles with `pdflatex` where it is available in CI.
- [x] 9.2 Write `prompts/research.md`, the `research` skill in `skills/research/` and `.claude/skills/research/`, and recipes for claim extraction and triage. Add the optional slice step to `prompts/prove.md` and the `prove` skill (D10). Verify by the documented commands running in `tests/recipes/` and by the skill listing in the plugin manifest.
- [ ] 9.3 Run the workflow end to end on a fixture chapter (a small LaTeX file with a convention, a lemma formalized in `VeriphyTest`, and a theorem that depends on it): extract, validate, export, reason, levels, impact, slice, appendix. Verify in the integration job that every step succeeds and that the appendix holds the verdict `entailed`.

## 10. Integration

- [ ] 10.1 Add `veriphy.graph` and the `graph` extra to the Project Profile in `openspec/constitution.md`, add the components row, and add the changelog entry. Verify with `nox -s docs`.
- [x] 10.2 Add the CLI and API parity test for `veriphy.graph`. Verify with pytest.
- [ ] 10.3 Run the full gate in order (formatting, checks, docs, tests, Lean tests) and the integration job. Verify that every session is green.

## Workflow follow-up

- Archive the change once CI is green, and release it as a minor version.
