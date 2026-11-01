# Tasks

## 1. Setup on first use (certified-graph-reasoning)

- [ ] 1.1 Pin `PINNED_COMMIT` and the prebuilt `oo-horn` hash, and add `ensure_release` that clones the tag and refuses a commit mismatch (D4). Verify with pytest on a fake release repository: a matching commit, and a moved tag that is refused with both commits named.
- [ ] 1.2 Import the reasoner from `<cache>/python/src` in the engine, with `run_reasoner` taking the source directory, and drop the run-time pip install from `checker build` (D1). Verify with pytest that the reasoner imports from a fake release's source and that no package is installed.
- [ ] 1.3 Add the prebuilt download on Linux x86_64 with both hash checks, the `oo-horn rules` probe and the fallback to a build, through `_process` (D3). Verify with pytest on a fake release directory: a good binary kept, a tampered binary deleted with both hashes named, and a failing probe that falls back to the build.
- [ ] 1.4 Call `ensure_reasoner` and `ensure_checker` from reasoning, honour `VERIPHY_GRAPH_SETUP=off`, report setup failures as unchecked with the failing step, and print setup messages only when something is set up (D2). Verify with pytest for: first use sets up and reports the verdict, a second run prints nothing, setup off gives an unchecked run with no fetch, and a failed setup gives an unchecked run naming the step.
- [ ] 1.5 Update the `tests` nox session and the CI integration job: fetch the release before pytest, run pytest with setup off, and run the fixture-chapter workflow with an empty cache (D5). Verify with a green CI run whose workflow step shows the first-use messages and the verdict `entailed`.

## 2. Documentation

- [ ] 2.1 Update the README: the graph in "What Veriphy provides", the one install command as an optional setup step, a usage block, and the `research` skill in the skills section and the manual copy (D6). Verify that every `python -m veriphy.graph` command in the README is a real command, with `tests/recipes/test_research.py` extended to the README.
- [ ] 2.2 Update the user guide's setup section, `prompts/research.md` and both copies of the `research` skill to the single install command and `VERIPHY_GRAPH_SETUP`. Verify with `nox -s docs` and the research document tests.

## 3. Integration

- [ ] 3.1 Run the full gate in order (formatting of the changed files, checks, docs, tests) and the integration job. Verify that every session is green.

## Workflow follow-up

- Archive the change, and release it as a patch or minor version as the user decides.
