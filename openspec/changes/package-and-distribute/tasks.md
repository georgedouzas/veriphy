# Tasks

## 1. Template baseline

- [x] 1.1 Create branch `package-and-distribute`. Run `copier copy --vcs-ref 2.0.1 gh:georgedouzas/copier-modern-python .` with the D1 answers, asking the author for the license and copyright holder. Verify that `.copier-answers.yml` records `_src_path: gh:georgedouzas/copier-modern-python`, `_commit: 2.0.1` and those answers.
- [x] 1.2 Restore Veriphy's own `README.md` from `HEAD`. Take the template's `openspec/config.yaml` (Veriphy's held only `schema:`) and keep `openspec/constitution.md` as binding (D8), filling in its Project Profile for Veriphy. Merge `.gitignore` (keep `/.lake/` and add the template's Python entries). Verify with `git diff --stat HEAD` that no Lean file, spec or Veriphy doc changed, and that `lake build` still passes.
- [x] 1.3 Commit the template baseline on its own. Verify that `copier update --defaults` immediately afterwards reports no changes.

## 2. Daemon as the `veriphy` package (daemon-package, constitution D2/D8)

- [x] 2.1 Create the D2 layout. Move the daemon code out of `sage_bridge/server.py` into the `core`, `oracle` and `sage_server` subpackages, and delete `sage_bridge/`. Make `veriphy` and `veriphy.core` Sage-free, re-exporting `__version__` and the errors with `__all__`. Add `veriphy.sage_server/__main__.py`. Verify that `python -c "import veriphy; print(veriphy.__version__)"` works in the plain uv venv and that `sage -python -m veriphy.sage_server` answers `ping` after `sage -pip install -e .`.
- [x] 2.2 Port the 38 unittest cases to pytest under a mirrored test tree (`tests/core`, `tests/oracle`, `tests/sage_server`), named `test_<function>_<behavior>` with one-line docstrings, using only public imports, and run `nox -s tests` on Sage's interpreter (D3). Verify that the whole ported suite passes before any further refactoring.
- [x] 2.3 Named exceptions: define `VeriphyError` and its subclasses in `core/_errors.py`, and replace every bare `ValueError`/`TypeError` raise and `MethodError`/`ParamError`/`ScriptError` in the oracle with the named ones, building each message in a variable. Error texts on the wire are unchanged (`<method>: <reason>`). Verify that the suite stays green and that `grep -rn "raise ValueError\|raise TypeError" src/` is empty.
- [x] 2.4 Add complete type annotations, docstrings for every module, class and function (with Args/Returns/Raises on public ones) and runnable doctests on the public API. Remove explanatory comments, and order modules per the constitution. Verify that `nox -s checks -- all` (ruff, mypy, bandit, interrogate, pydoclint, deptry, pip-audit, configured as in 2.6) passes, and that `nox -s tests` runs the doctests green.
- [x] 2.5 Guard Sage in `sage_server._main.main` (the lazy import of `veriphy.oracle` with a reasoned suppression, the "must run under SageMath" message, exit status 2), add the `veriphy-sage-server` script, and add the `veriphy` version to every response envelope and `ping`. Add tests for the envelope version and for a no-Sage start in a plain-Python subprocess. Verify that `uv run veriphy-sage-server </dev/null` exits 2 with the message, and that `echo '{"id":1,"method":"ping"}' | sage -python -m veriphy.sage_server` shows `ok`, `sage` and `veriphy`.
- [x] 2.6 Configure `pyproject.toml` for the Sage-only code: deptry ignores `sage`, mypy `ignore_missing_imports` for `sage.*`, and the `tests` nox session on Sage's interpreter with system site-packages. Verify that `nox -s checks -- all` and `nox -s tests` both pass, and that `lake build VeriphyTest` passes against the refactored daemon.

## 3. Bridge resolution (daemon-resolution)

- [x] 3.1 In `Bridge.lean`, add `Config.resolve` (D4 order: `VERIPHY_SAGE_CMD`, then `VERIPHY_SAGE_SERVER` with an existence check, then `-m veriphy.sage_server`). Verify that `lake build VeriphyTest` passes with neither variable set after `sage -pip install -e .`.
- [x] 3.2 Make start-up failures actionable: a spawn failure names `VERIPHY_SAGE_CMD`; an empty first line reads stderr (truncated) and maps a missing module to `sage -pip install veriphy`; a stale `VERIPHY_SAGE_SERVER` names the variable and the path. Verify with three scratch-file checks: `sage -pip uninstall veriphy`, `VERIPHY_SAGE_CMD=/nonexistent`, and `VERIPHY_SAGE_SERVER=sage_bridge/server.py`, each producing the specified message. Reinstall afterwards.
- [x] 3.4 Verify the downstream path. Create a scratch Lake project (in the scratchpad) that requires Veriphy from this checkout, and run one `sage_lincomb` example with no Veriphy environment variables, which must close the goal. Then build its emitted replacement with Sage off `PATH`, which must succeed.

## 4. Versioning and CI (releases)

- [ ] 4.2 Adapt `.github/workflows/ci.yml` (D6): add the `lean` job (no Sage: `lake build`, `lake build VeriphyTest.Kit`) and the `integration` job (pinned `sagemath/sagemath` 10.x image, wheel install, pytest, `lake build VeriphyTest`, caches). Keep the template's `checks` job. Verify by validating the YAML with `actionlint`, then pushing the branch and confirming all jobs pass on GitHub Actions (a push of a non-default branch, which the author approves when we get there).

## 5. Documentation and plugin

- [x] 5.1 Rewrite the README Setup as three install steps (SageMath, `sage -pip install veriphy`, a Lake `require … rev = "X.Y.Z"`), plus a "Developing Veriphy" section (`sage -pip install -e .`, nox sessions, `copier update`, `VERIPHY_SAGE_SERVER` for daemon work). Verify that each command in the section runs as written in a fresh shell.
- [x] 5.2 Update `skills/prove/SKILL.md` and `prompts/prove.md` setup checks to `sage -python -m veriphy.sage_server`, and drop the `VERIPHY_SAGE_SERVER` instruction. Correct the `plugin.json` and `marketplace.json` descriptions (seven tactics plus `sage_certify`), and recommend installing the plugin from the git URL. Verify by running the skill's documented ping command.
- [x] 5.3 Document distribution (three channels, one tag) and record passagemath as future work. Move `docs/DESIGN.md` into the template's docs locations (`docs/overview/user_guide.md` for the design rationale, `docs/development/index.md` for setup, adding a certificate and future work) and delete it. Verify that `nox -s docs -- build` succeeds.

## 6. Integration check

- [ ] 6.1 From a clean clone of the branch: `uv build`, `sage -pip install dist/*.whl`, `lake build`, `lake build VeriphyTest`, `nox -s tests`, `nox -s checks -- all`. Verify that all are green, and record the outputs in the PR description.

## 7. PyPI publishing (last)

- [x] 7.1 Keep the template-generated `.github/workflows/release.yml` unchanged: it already runs the reusable CI (including the `lean` and `integration` jobs) before `build`, then the GitHub release and trusted publishing through `pypa/gh-action-pypi-publish`, with no token. Release tags follow the template's `X.Y.Z` pattern (no `v`). Verified: `actionlint` passes, and `git diff` against the template baseline is empty.
- [ ] 7.2 Dry-run the release build: in a throwaway clone tagged `0.4.0`, `uv build` produces `veriphy-0.4.0*.whl`. Verify that `sage -pip install` of that wheel answers `ping` with `"veriphy": "0.4.0"`.
- [ ] 7.3 Run `openspec validate package-and-distribute --strict` and verify that it passes.

## Workflow follow-up

- The author registers the PyPI trusted publisher (project `veriphy`, repository `georgedouzas/veriphy`, workflow `release.yml`, environment as in the template) on pypi.org.
- Merge the branch to `main`, then tag and push `0.4.0`. The release workflow publishes to PyPI and creates the GitHub release. Confirm `sage -pip install veriphy==0.4.0` and a downstream Lake `require` at `0.4.0` work.
- Archive the change with `/opsx:archive`.
