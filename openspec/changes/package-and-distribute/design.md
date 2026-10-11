# Design

## Context

The motivation is in proposal.md (Why). The current state below shapes the approach.

- **Repo root holds the Lean project.** `lakefile.toml`, `lean-toolchain`, `Veriphy/` and `VeriphyTest/` are at the root, and the Lake `require` mechanism needs them there. Python lives in a loose `sage_bridge/` with no packaging.
- **The bridge spawns one process per request.** `Veriphy/Bridge.lean` spawns `cfg.sageCmd -python <serverPath>` for every request, with `sageCmd := "sage"` and the server path from `VERIPHY_SAGE_SERVER` or a relative default. If the child dies, `getLine` returns `""` and the user sees a JSON parse error.
- **Sage on this machine.** It is 10.9 on Python 3.14.3. `sage -pip` works, and its scripts directory (`/var/tmp/sage-10.9-current/local/bin`) is **not** on `PATH`, so a console script installed into Sage cannot be the default command. `python -m` under `sage -python` always works.
- **The template.** `copier-modern-python` 2.0.1 (`_subdirectory: project`) generates:
  - `pyproject.toml` (hatchling + hatch-vcs with uv; dynamic version), `src/<pkg>/{__init__.py,py.typed}`, `tests/`;
  - `noxfile.py` with sessions `checks` (ruff, mypy, bandit, interrogate, pydoclint, pip-audit, deptry), `tests` (pytest + coverage), `docs`, `formatting`, `changelog` and `release`;
  - `.github/workflows/{ci,doc,release}.yml`, properdocs docs, `renovate.json`, pre-commit, LICENSE, and an `openspec/` scaffold.

  Its default Python range is `>=3.11, <3.14`, which excludes Sage's 3.14.
- **External state.** PyPI `veriphy` is unclaimed. The GitHub remote is `georgedouzas/veriphy`, there are no tags, and `plugin.json` says 0.3.0.

## Goals / Non-Goals

**Goals:**
- A user installs with `sage -pip install veriphy`, a Lake `require … @ "X.Y.Z"`, and optionally the plugin, without cloning or setting environment variables.
- The repo is generated from and kept in sync with the author's template.
- Every release is CI-proven, including the full tactic suite against the built wheel, and carries one version everywhere.

**Non-Goals:**
- Making the daemon installable without Sage (passagemath). The author chose "inside existing Sage". The package is structured so a later change can add that (D2).
- A persistent daemon. Still DESIGN.md §8 future work.
- conda-forge or Docker images of Veriphy.
- Changing tactics, the protocol (beyond additive version fields) or the trust model.

## Decisions

### D1. Apply the template in place, then restore Veriphy's files

Run `copier copy --vcs-ref 2.0.1 gh:georgedouzas/copier-modern-python .` on a branch, with these answers:
- `project_layout=library`, `package_manager=uv`, `publish_pypi=true`, `git_provider=GitHub`;
- `repository_namespace=georgedouzas`, `repository_name=veriphy`, `python_package_distribution_name=veriphy`, `python_package_import_name=veriphy`;
- `python_versions=">=3.11, <3.15"`, `spec_tool=openspec`, `include_dockerfile=false`;
- the license and holder as the author chooses.

Then use `git checkout -p`/`git restore` to keep Veriphy's own versions of `README.md`, `openspec/config.yaml` and `.gitignore`, merged by hand (the Lean `/.lake/` entry plus the template's Python entries). The template's `openspec/constitution.md` is kept if it adds value.

Because the template comes from the remote repository, `.copier-answers.yml` records `_src_path: gh:georgedouzas/copier-modern-python`, so `copier update` pulls new template tags from GitHub and never depends on a local checkout. It does a three-way merge from the recorded answers and template version, so local edits made after this commit survive later updates as ordinary diffs.

Applying it surfaced a template bug: the generated `docs/generate_api.py` called `Path.relative_to` with several parts, which Python 3.14 rejects. It was fixed upstream and released as template 2.0.2, and the repo was moved to 2.0.2 with `copier update`, which merged cleanly.

*Alternative:* generate into a temp directory and copy over selected files. Rejected: there would be no `.copier-answers.yml` baseline that matches the repo, so every later `copier update` would re-propose the skipped files as conflicts.

### D2. Package layout and Sage isolation (constitution-shaped)

The author adopted the template's `openspec/constitution.md` as binding and asked for compliance in this change (D8). It fixes the package shape: subpackages only at the top level, shared leaves in `core`, private implementation modules, `__all__` surfaces, and imports that run downward.

```
src/veriphy/__init__.py                 docstring + __all__: __version__, the errors (Sage-free)
src/veriphy/core/__init__.py            re-exports __version__ and the named exceptions
src/veriphy/core/_errors.py             VeriphyError, ParamError, MethodError, ScriptError, CertificateError,
                                        SageUnavailableError
src/veriphy/core/_version.py            __version__ via importlib.metadata
src/veriphy/oracle/__init__.py          the Sage-backed surface: METHODS, method, coercers, encode, exact_lp, handle
src/veriphy/oracle/_registry.py         @method, the coercers, METHODS
src/veriphy/oracle/_encoding.py         encode, poly_to_terms
src/veriphy/oracle/_lp.py               exact_lp
src/veriphy/oracle/_certificates.py     factor, sos, roots, lincomb, sum, farkas, exists
src/veriphy/oracle/_scripts.py          run_script, certify (and the shared script runner)
src/veriphy/oracle/_symbolic.py         symbolic_check, solve, matrix_check
src/veriphy/oracle/_protocol.py         handle (one request line to one response)
src/veriphy/sage_server/__init__.py     surface package: re-exports main alone
src/veriphy/sage_server/__main__.py     `python -m veriphy.sage_server`
src/veriphy/sage_server/_main.py        main: the lazy import of `veriphy.oracle` (Sage), the stdio loop
tests/…                                 mirrors src/ (core/, oracle/, sage_server/), pytest, test_<function>_<behavior>
```

- `veriphy` and `veriphy.core` never import Sage. `veriphy.oracle` does, at module top.
- `sage_server._main.main` imports `veriphy.oracle` lazily. This is the constitution's one allowed lazy import, deferring an optional dependency, and it carries a suppression with that reason. If the import fails, `main` raises nothing: it prints the "must run under SageMath" message and exits with status 2.
- `[project.scripts] veriphy-sage-server = "veriphy.sage_server:main"`.
- Sage is not a dependency. deptry ignores the `sage` import (DEP001), and mypy gets `ignore_missing_imports` for `sage.*`.
- The protocol, method names, parameters and result shapes are unchanged (daemon-package spec). Only the code's organization, typing, docstrings and exception types change.

### D3. Development and test environments against Sage's interpreter

The `tests` nox session runs on Sage's Python:
- `python=SAGE_PYTHON`, resolved once with `sage -python -c "import sys; print(sys.executable)"`;
- `venv_params=["--system-site-packages"]`, so the venv sees Sage's site-packages.

The template's other sessions (`checks` quality/security/docs, `formatting`, `docs`) keep the plain venv, because they never import Sage. Types run in the plain venv with the mypy override.

For local development: `sage -pip install -e .`. That makes `sage -python -m veriphy.sage_server` resolve to the working tree, so `lake build VeriphyTest` exercises current code without `VERIPHY_SAGE_SERVER`.

*Alternative:* run all tooling with `sage -pip`. Rejected because it pollutes Sage's environment with dev tools and diverges from the template's uv flow.

### D4. Bridge resolution, start-up diagnostics and version check (`Veriphy/Bridge.lean`)

`Config.resolve : IO (String × Array String)` picks the command:
1. `exe := $VERIPHY_SAGE_CMD` or `"sage"`.
2. If `$VERIPHY_SAGE_SERVER` is set, check that the path exists (otherwise an error naming the variable and the path) and run `exe -python <path>`.
3. Otherwise run `exe -python -m veriphy.sage_server`.

`request` handles failures:
- A spawn failure becomes "could not start Sage (`<exe>`); install SageMath or set VERIPHY_SAGE_CMD".
- An empty first stdout line means the daemon died. `request` reads stderr, truncated to 2 KB. If stderr contains `No module named 'veriphy'`, the error says to `sage -pip install veriphy`; otherwise it reports the stderr. A non-JSON first line is treated the same way, and the executable is checked to exist (a path, or a name on `PATH`) before spawning.


### D5. Versioning

Versioning is left to hatch-vcs: the tag `X.Y.Z` is the only place a version is written, and the Python version is derived from it. The Lean library carries no version constant, since Lake consumers pin the same tag as `rev`, and nothing compares Lean and daemon versions at run time. The daemon still reports hatch's version in `ping` and each envelope, purely as information. The first release is `0.4.0`.

### D6. CI layout (`.github/workflows/ci.yml`, adapted from the template)

- **lean:** `ubuntu-latest`, no Sage. Runs `leanprover/lean-action` with `lake exe cache get`, then `lake build` and `lake build VeriphyTest.Kit`.
- **checks:** the template's quality/types/dependencies/security/docs matrix, unchanged apart from config (D2).
- **integration:** a container `sagemath/sagemath:<10.x tag>`. The exact tag is pinned while applying, to the newest 10.x image available. Steps:
  1. `uv build`, then `sage -pip install dist/*.whl`;
  2. `sage -python -m pytest tests`;
  3. install elan, `lake exe cache get`, `lake build VeriphyTest` (replay is on in the file).

  `.lake` and `~/.elan` are cached with `actions/cache` keyed on `lake-manifest.json`.

**PyPI comes last and uses the template's own support.** Answering `publish_pypi=true` already gives `release.yml` (uv build → GitHub release → `pypa/gh-action-pypi-publish` with trusted publishing). Veriphy adds nothing to it: its `build` job already `needs` the reusable `ci.yml`, which now includes the `lean` and `integration` jobs. Release tags follow the template's pattern, `X.Y.Z` without a `v`.

Nothing else about publishing is custom. It is the final implementation step, after packaging, the bridge, CI and docs are proven locally and on Actions. The one-time trusted-publisher registration on pypi.org and the first tag are the author's follow-up.

### D7. Docs and plugin

- README Setup becomes three steps: SageMath, `sage -pip install veriphy`, and a Lake `require`. A "Developing Veriphy" section covers `sage -pip install -e .`, nox and `copier update`.
- The `prove` skill's installation check becomes `echo '{"id":1,"method":"ping"}' | sage -python -m veriphy.sage_server`. Its `VERIPHY_SAGE_SERVER` instruction is dropped.
- The plugin description is corrected (seven tactics plus `sage_certify`). The README recommends installing the plugin from the git URL, not a local clone, which avoids copying `.lake/`.
- The template's properdocs site includes `docs/DESIGN.md` in its nav.

### D8. Constitution adoption

- Keep the template's `openspec/constitution.md` and its `config.yaml` `context:` line, which makes it binding.
- Fill in the Project Profile for Veriphy:
  - the ecosystem contract is the daemon's JSON-lines protocol and the `certificates/*` and `distribution/*` specs;
  - surface packages: `veriphy.sage_server` (a runner) and `veriphy.oracle` (an importer);
  - Sage is an optional, undeclared runtime that is always lazily imported;
  - the Lean code follows mathlib conventions and is gated by `lake build`/`VeriphyTest`, not by the Python gate.
- The Python rules apply to `src/` and `tests/`.
- The daemon is refactored to comply as part of this change: the layout (D2), named exceptions from `core`, complete type annotations under mypy, docstrings with Args/Returns/Raises, doctests on the public API (run under Sage), no explanatory comments, and the test tree mirroring the source tree.
- Behavior is pinned by the existing 38 tests, ported first and kept green through the refactor.

## Risks / Trade-offs

- **[Risk]** The in-place `copier copy` overwrites Veriphy files. → Do it on a branch, review `git diff` file by file, and use `git restore` for README, OpenSpec config and Lean files. A task lists exactly which files to keep.
- **[Risk]** The SageMath Docker image (several GB) makes the integration job slow. → Pin the image tag (`10.10`) and cache `~/.elan` and `.lake`. It runs on every push, so branch pushes are verified before merge.
- **[Risk]** Template tooling (pip-audit, deptry, interrogate) objects to the Sage-only module (missing docstrings, an undeclared `sage` import). → Configure exclusions in `pyproject.toml` rather than weaken the template. Docstring coverage is met by adding docstrings where they are missing.
- **[Risk]** Users with an older Sage (Python < 3.11) cannot install. → This is documented. `requires-python >=3.11` matches the template minimum, and Sage 10.x ships Python 3.11 or newer.
- **[Risk]** The compliance refactor of a ~700-line daemon could change behavior. → Port the existing tests first (names and structure per the constitution) and keep them green after every step. The Lean suite (`lake build VeriphyTest`) is the end-to-end check.
- **[Trade-off]** "Inside existing Sage" keeps users installing SageMath themselves, a multi-GB step. This was accepted for certainty. D2 leaves room for a passagemath route later.

## Migration Plan

1. Branch, run copier, restore Veriphy files, and commit the template baseline.
2. Move the daemon and tests into `src/`/`tests/`, then `sage -pip install -e .`.
3. Change the bridge (D4). `lake build VeriphyTest` must pass with no environment variables set.
4. Versions, CI and docs.
5. Last: wire PyPI publishing (the template's `release.yml` plus the CI gate). Then the author merges, registers the trusted publisher and tags `0.4.0`.

Rollback before tagging is a branch revert. After tagging, a broken release is yanked on PyPI and fixed with `0.4.1`. Lake users simply pin the previous rev.

Developers' existing `VERIPHY_SAGE_SERVER=…/sage_bridge/server.py` stops working, and the error says so (spec: stale development path).

## Open Questions

- The license and copyright holder (answered by the author during the copier run). Every task works with any choice.
- The exact `sagemath/sagemath` image tag, pinned while applying to the newest 10.x tag published.
