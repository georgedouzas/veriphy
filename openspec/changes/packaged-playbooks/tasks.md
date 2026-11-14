# Tasks

## 1. Move and package

- [x] 1.1 Move `prompts/` to `src/veriphy/prompts/` with `git mv`, and force-include `lean/assets/VeriphyAssets/` in the wheel as `veriphy/prompts/assets/VeriphyAssets/` (D1, D3). Verify with `uv build` that the wheel lists `veriphy/prompts/prove.md`, every template and both assets, and that `--doctest-modules` collects no new item (D6).
- [x] 1.2 Add `veriphy.prompts` with `path`, `list`, `show` and `copy`, including the editable-install fallback for assets (D2, D3). Verify with pytest in `tests/prompts/`: each subcommand, an optional extension, an unknown name with its closest matches and status 1, a copy into a workspace, the refusal to overwrite, and the asset fallback.

## 2. Callers

- [x] 2.1 Update the template paths in `lean/VeriphyTest/*.lean` and `lean/coverage/PhyslibRecipes.lean` (D5). Verify with `lake build VeriphyTest.Kit`, and with the Sage-backed `lake build VeriphyTest` in the gate.
- [x] 2.2 Rewrite both copies of the three skills to ask the package (D4), and update `tests/recipes/` to read from the package and to check that the two copies are identical. Verify with pytest.
- [x] 2.3 Update the README (manual install without a clone or `VERIPHY_HOME`, links to playbooks), the user guide, the developer guide, the constitution's scope and every recipe or playbook that names a repository path. Verify with `git grep` that no tracked file outside the archive and the changelog names `prompts/` without `src/veriphy/`, and with `uv run nox -s docs -- build`.

## 3. Integration

- [x] 3.1 Run the gate (checks, tests, the Sage-backed `lake build VeriphyTest`) and CI on the branch, and install the built wheel into Sage on a path with no clone to run `python -m veriphy.prompts show prove`. Verify that every session and job is green and that the command prints the playbook.

## Workflow follow-up

- Archive the change and release it as a minor version, with release notes saying that manual installs no longer use `VERIPHY_HOME`.
