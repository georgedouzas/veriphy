# Design

## Context

See proposal.md for the motivation. Today `checker build` (`veriphy.graph._checker.build_checker`) clones Open
Ontologies `v2.1.0` into `~/.cache/veriphy/open-ontologies/v2.1.0`, pip-installs its `python/` package into the
running interpreter, and runs `lake build oo-horn`. `find_checker` looks only at `VERIPHY_OO_HORN` and the cache. The
release ships a prebuilt `oo-horn` for Linux x86_64 only, listed in its `SHASUMS.txt`
(`967224162167ddfa55dd3196e86ea719157f121b62981f283c0315381da0477b`). The tag points to commit
`ef6e781c71aaccaa35c2a1cd06169f0c862d5769`. The `open_ontologies_lite` package needs only `pyoxigraph`, which the extra
installs. Tests must not reach the network.

## Goals / Non-Goals

**Goals:**

- `sage -pip install 'veriphy[graph]'` is the only installation step.
- Nothing is written into the Python environment after installation.
- Every fetched artifact is checked against a value Veriphy pins.

**Non-Goals:**

- Prebuilt checkers for other platforms. The release ships none, and building stays the fallback.
- Changes upstream, or copying the reasoner into Veriphy.

## Decisions

### D1. The reasoner is imported from the cached source

The engine puts `<cache>/python/src` first on `sys.path` before it imports `open_ontologies_lite.horn`, and drops a
previously imported `open_ontologies_lite` from `sys.modules` when that one lacks `horn` (the PyPI 0.5.0 package). The
alternative, pip-installing at run time, writes into Sage's environment behind the user's back and needs pip or uv in
that environment, which the Sage venv of the test session does not have. `run_reasoner` takes the source directory as
a parameter, so the engine performs no setup itself.

### D2. Setup lives in `_checker`, and runs from `_reasoning`

`_checker` gains `ensure_release`, `ensure_reasoner` and `ensure_checker`. Each takes the environment and a `notify`
callback for its messages, which default to `os.environ` and standard error. `reason_triples` calls `ensure_reasoner`
before the run, and `_check` calls `ensure_checker` when `find_checker` finds nothing. `VERIPHY_GRAPH_SETUP=off` makes
both return what is cached and set up nothing. A setup failure from `ensure_checker` becomes an `unchecked_error`
report with the failing step. A setup failure from `ensure_reasoner` raises `GraphExtraMissingError`, now naming the
setup command and the cause.

### D3. Prebuilt checker on Linux x86_64

On `sys.platform == 'linux'` with an `x86_64` or `amd64` machine, `ensure_checker` downloads
`oo-horn-x86_64-unknown-linux-gnu` and `SHASUMS.txt` from the release. It keeps the binary only when its SHA-256 equals
both the pinned hash and the listed hash, and only when `oo-horn rules` then runs. Otherwise it deletes the binary
and builds as today. The binary lands at `<cache>/bin/oo-horn`, and `find_checker` looks there before the built
binary. The pinned hash makes a replaced release asset fail even when its `SHASUMS.txt` was replaced too. The download
goes through `veriphy.graph._process` with `urllib`, so all external effects stay in one module, and the release base
URL is a parameter, so tests serve a fake release from a local directory.

### D4. Pinned commit

After the clone, `git rev-parse HEAD` must equal `PINNED_COMMIT`. On a mismatch the clone is deleted and setup fails
naming both commits. This catches a moved tag, which the tag name alone does not.

### D5. Test session and CI

The `tests` nox session fetches the release before pytest (`checker build --reasoner-only`, which now only clones and
verifies) and runs pytest with `VERIPHY_GRAPH_SETUP=off`, so no test reaches the network. Setup tests use a fake
release: a local git repository and a directory of fake assets. The integration job keeps its explicit build step,
which now downloads the checker. Its fixture-chapter workflow runs with an empty `XDG_CACHE_HOME`, so it exercises
real first-use setup end to end.

### D6. README

The README gains the graph in "What Veriphy provides", an optional setup step with the one install command, a short
usage block (`validate`, `reason`, `levels`, `appendix`, `#veriphy_graph`), and the `research` skill in the skills
section and the manual copy.

## Risks / Trade-offs

- [First use takes minutes on macOS, where the checker is built] → The message says so before the build starts, and
  `checker build` lets a user do it ahead of time.
- [The prebuilt binary may not run on an old glibc] → `oo-horn rules` must run before the binary is kept, and setup
  falls back to the build.
- [Editing `sys.path` changes import resolution for the process] → Only the cached release's `python/src` is added,
  only once, and only when the reasoner is first needed.
- [A user who wanted no network access during a run] → `VERIPHY_GRAPH_SETUP=off`, documented in the README and the
  user guide.
