# Tasks

## 1. Template baseline

- [ ] 1.1 Create branch `package-and-distribute`. Run `copier copy --vcs-ref 2.0.1 gh:georgedouzas/copier-modern-python .` with the D1 answers, asking the author for the license and copyright holder. Verify that `.copier-answers.yml` records `_src_path: gh:georgedouzas/copier-modern-python`, `_commit: 2.0.1` and those answers.
- [ ] 1.2 Restore Veriphy's own files from `HEAD` (`README.md`, `openspec/config.yaml`, the Lean sources, `lakefile.toml`, `docs/DESIGN.md`). Merge `.gitignore` (keep `/.lake/` and add the template's Python entries). Keep or drop the template `openspec/constitution.md` by reading it. Verify with `git diff --stat HEAD` that no Lean file, spec or Veriphy doc changed, and that `lake build` still passes.
- [ ] 1.3 Commit the template baseline on its own. Verify that `copier update --defaults` immediately afterwards reports no changes.

## 2. Daemon as the `veriphy` package (daemon-package)

- [ ] 2.1 `git mv sage_bridge/server.py src/veriphy/sage_server.py` and `sage_bridge/test_server.py tests/test_sage_server.py`. Make `src/veriphy/__init__.py` expose `__version__` through `importlib.metadata`, with no Sage import. Verify that `python -c "import veriphy; print(veriphy.__version__)"` works in the plain uv venv.
- [ ] 2.2 Guard the Sage imports in `sage_server.py` so that `main()` exits with status 2 and the "must run under SageMath" message when Sage is absent, and add the `veriphy-sage-server` script to `pyproject.toml`. Verify that `uv run veriphy-sage-server </dev/null` prints that message and exits 2.
- [ ] 2.3 Add the `veriphy` version to every response envelope and to `ping`'s result (additive, per the modified `certificates/oracle-methods` requirement). Verify with `echo '{"id":1,"method":"ping"}' | sage -python -m veriphy.sage_server` after `sage -pip install -e .`, which must show `ok`, `sage` and `veriphy`.
- [ ] 2.4 Convert the tests to pytest (the existing unittest classes are kept as pytest-collected tests, and `sys.path` hacks are removed). Add tests for the envelope version and for a no-Sage start in a subprocess using plain Python. Verify that `nox -s tests` (D3: Sage interpreter, system site-packages) passes on all 38 existing tests plus the new ones.
- [ ] 2.5 Configure `pyproject.toml` for the Sage-only module: deptry ignores the `sage` import, mypy gets `ignore_missing_imports` for `sage.*`, and the bandit and interrogate exclusions or docstring additions as needed. Verify that `nox -s checks -- all` passes in the plain venv.

## 3. Bridge resolution (daemon-resolution)

- [ ] 3.1 Add `Veriphy/Version.lean` (`def Veriphy.version : String := "0.4.0"`). In `Bridge.lean`, add `Config.resolve` (D4 order: `VERIPHY_SAGE_CMD`, then `VERIPHY_SAGE_SERVER` with an existence check, then `-m veriphy.sage_server`). Verify that `lake build VeriphyTest` passes with neither variable set after `sage -pip install -e .`.
- [ ] 3.2 Make start-up failures actionable: a spawn failure names `VERIPHY_SAGE_CMD`; an empty first line reads stderr (truncated) and maps a missing module to `sage -pip install veriphy==<version>`; a stale `VERIPHY_SAGE_SERVER` names the variable and the path. Verify with three scratch-file checks: `sage -pip uninstall veriphy`, `VERIPHY_SAGE_CMD=/nonexistent`, and `VERIPHY_SAGE_SERVER=sage_bridge/server.py`, each producing the specified message. Reinstall afterwards.
- [ ] 3.3 Record the daemon version from the envelope (an `initialize` `IO.Ref`). In `Kit.run`, warn once per process on a mismatch with `Veriphy.version`. Verify with a scratch file and `VERIPHY_SAGE_SERVER` pointing at a copy of the daemon patched to report `0.3.9`: one warning naming both versions, and the tactic still succeeds.
- [ ] 3.4 Verify the downstream path. Create a scratch Lake project (in the scratchpad) that requires Veriphy from this checkout, and run one `sage_lincomb` example with no Veriphy environment variables, which must close the goal. Then build its emitted replacement with Sage off `PATH`, which must succeed.

## 4. Versioning and CI (releases)

- [ ] 4.1 Add `scripts/check_versions.py`, which compares the `Veriphy/Version.lean` constant, `plugin.json` and, with `--tag vX.Y.Z`, the tag, and names the mismatched file. Bump `plugin.json` to `0.4.0`. Verify that it passes now, fails with a temporary `plugin.json` edit, and that `--tag v0.4.1` fails.
- [ ] 4.2 Adapt `.github/workflows/ci.yml` (D6): add the `lean` job (no Sage: `lake build`, `lake build VeriphyTest.Kit`, `check_versions.py`) and the `integration` job (pinned `sagemath/sagemath` 10.x image, wheel install, pytest, `lake build VeriphyTest`, caches). Keep the template's `checks` job. Verify by validating the YAML with `actionlint`, then pushing the branch and confirming all jobs pass on GitHub Actions (a push of a non-default branch, which the author approves when we get there).

## 5. Documentation and plugin

- [ ] 5.1 Rewrite the README Setup as three install steps (SageMath, `sage -pip install veriphy==X.Y.Z`, a Lake `require … rev = "vX.Y.Z"`), plus a "Developing Veriphy" section (`sage -pip install -e .`, nox sessions, `copier update`, `VERIPHY_SAGE_SERVER` for daemon work). Verify that each command in the section runs as written in a fresh shell.
- [ ] 5.2 Update `skills/prove/SKILL.md` and `prompts/prove.md` setup checks to `sage -python -m veriphy.sage_server`, and drop the `VERIPHY_SAGE_SERVER` instruction. Correct the `plugin.json` and `marketplace.json` descriptions (seven tactics plus `sage_certify`), and recommend installing the plugin from the git URL. Verify by running the skill's documented ping command.
- [ ] 5.3 Update `docs/DESIGN.md`: §8 (packaging done; passagemath recorded as a future option) and a short "Distribution" section (three channels, one tag). Add `DESIGN.md` to the properdocs nav. Verify that `nox -s docs -- build` succeeds.

## 6. Integration check

- [ ] 6.1 From a clean clone of the branch: `uv build`, `sage -pip install dist/*.whl`, `lake build`, `lake build VeriphyTest`, `nox -s tests`, `nox -s checks -- all`, `python scripts/check_versions.py`. Verify that all are green, and record the outputs in the PR description.

## 7. PyPI publishing (last)

- [ ] 7.1 Keep the template-generated `.github/workflows/release.yml` (uv build → GitHub release → trusted publishing through `pypa/gh-action-pypi-publish`, no token). Add only a `needs:` on the CI jobs and a `scripts/check_versions.py --tag "$GITHUB_REF_NAME"` step before the build. Verify with `actionlint`, and with `git diff` against the template's generated version showing only those two additions.
- [ ] 7.2 Dry-run the release build: in a throwaway clone tagged `v0.4.0`, `uv build` produces `veriphy-0.4.0*.whl` and `check_versions.py --tag v0.4.0` passes. Verify that `sage -pip install` of that wheel answers `ping` with `"veriphy": "0.4.0"`.
- [ ] 7.3 Run `openspec validate package-and-distribute --strict` and verify that it passes.

## Workflow follow-up

- The author registers the PyPI trusted publisher (project `veriphy`, repository `georgedouzas/veriphy`, workflow `release.yml`, environment as in the template) on pypi.org.
- Merge the branch to `main`, then tag and push `v0.4.0`. The release workflow publishes to PyPI and creates the GitHub release. Confirm `sage -pip install veriphy==0.4.0` and a downstream Lake `require` at `v0.4.0` work.
- Archive the change with `/opsx:archive`.
