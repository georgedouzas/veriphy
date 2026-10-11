# Proposal

## Why

Using Veriphy today means cloning the repo. The Lean side finds the daemon by a file path (`sage -python <path>/server.py`, overridden through `VERIPHY_SAGE_SERVER`), and the plugin route copies the whole repo, including an 8 GB `.lake/`, into the Claude plugin cache, which then needs `VERIPHY_HOME` to undo. Nothing is versioned: there are no tags, the plugin claims 0.3.0, and its description still lists five tactics. There is also no LICENSE, which blocks publishing on any index.

Packaging the daemon as a normal Python distribution and versioning all three parts together turns installation into three standard steps:
- `sage -pip install veriphy`;
- a Lake `require … @ "vX.Y.Z"`;
- `claude plugin install`.

## What Changes

- **Template adoption.** Apply the author's `copier-modern-python` template from its GitHub repository (`gh:georgedouzas/copier-modern-python`, 2.0.1, `library` layout, uv, PyPI publishing) in place. This adds `pyproject.toml`, `noxfile.py`, ruff/mypy/bandit/pytest configuration, properdocs docs, GitHub workflows, renovate, a LICENSE and `.copier-answers.yml`. The Lean project stays at the repo root next to them, and Veriphy's own README, `docs/DESIGN.md` and OpenSpec setup are kept. From then on, `copier update` tracks the template.
- **Daemon as a package.** `sage_bridge/server.py` becomes `src/veriphy/sage_server.py` in the `veriphy` distribution, runnable as `python -m veriphy.sage_server`, with a `veriphy-sage-server` console script for convenience. Sage is **not** a declared dependency: the package is installed into an existing Sage with `sage -pip install veriphy`. Its line protocol and methods are unchanged.
- **Daemon resolution in Lean.** By default the bridge now starts `sage -python -m veriphy.sage_server`, so a released install needs no paths or environment variables.
  - `VERIPHY_SAGE_CMD` overrides the Sage executable.
  - `VERIPHY_SAGE_SERVER` stays as a development override that points at a script.
  - If the daemon cannot start, for example because the package is not installed in Sage, the error names the fix instead of reporting a JSON parse failure.
- **Python tooling against Sage.** Tests and type checks need `sage.all`, so the development environment is a uv venv created from Sage's interpreter with system site packages. Lint, format and security checks also run in a plain venv. The daemon tests move to `tests/` under pytest.
- **CI split by need.**
  - A Sage-free Lean job: `lake build` and `lake build VeriphyTest.Kit`.
  - A Python checks job, which needs no Sage.
  - An integration job in a SageMath container: Python tests, `sage -pip install .`, `lake build VeriphyTest` with replay on.
- **One version, three channels.** A single `vX.Y.Z` git tag versions everything. The Python version comes from VCS. The tag is the Lake `rev`. PyPI publishing is the last step and reuses the template's release workflow (trusted publishing), adding only the version check and the CI gate.
- **Install docs.** README Setup becomes the three-step install. The `prove` skill checks the daemon with `sage -python -m veriphy.sage_server` instead of a repo path, and no longer needs a clone for proving outside the repo. The plugin description is corrected.
- **BREAKING (dev only):** `sage_bridge/server.py` moves. Anyone pointing `VERIPHY_SAGE_SERVER` at the old path must update it, or simply `sage -pip install -e .`.

## Capabilities

### New Capabilities
- `distribution/daemon-package`: the `veriphy` Python distribution: contents, entry points, how it runs inside Sage, and the protocol compatibility it guarantees.
- `distribution/daemon-resolution`: how the Lean bridge locates and starts the daemon (default command, overrides, and failure messages).
- `distribution/releases`: versioning across Lake, PyPI and the Claude plugin, release gating, and what CI must prove before a release.

### Modified Capabilities
- `certificates/oracle-methods`: "Method behavior is preserved" now allows additive result fields, so `ping` can report the package version alongside the Sage version. No other protocol change.

## Impact

- **New files:** `pyproject.toml`, `noxfile.py`, `.copier-answers.yml`, `LICENSE`, `.github/workflows/{ci,doc,release}.yml` (adapted), `renovate.json`, `properdocs.yml`, `.pre-commit-config.yaml`, `.editorconfig`, `CHANGELOG.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`.
- **Moved:** `sage_bridge/server.py` → `src/veriphy/sage_server.py`; `sage_bridge/test_server.py` → `tests/test_sage_server.py`.
- **Lean:** `Veriphy/Bridge.lean` (`Config`, process start, error on a failed start). No tactic changes.
- **Docs:** `README.md`, `skills/prove/SKILL.md`, `prompts/prove.md` (the setup check), `docs/DESIGN.md`, moved into `docs/overview/user_guide.md` and `docs/development/index.md`, `.claude-plugin/*.json`.
- **External:** a PyPI project `veriphy` (the name is currently free), trusted publishing configured on the GitHub repo `georgedouzas/veriphy`, and the first tag.
- **Needs a decision from the author while applying:** the license. The template asks for it and nothing can be published without it.
