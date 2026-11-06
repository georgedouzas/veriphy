# Tasks

## 1. Move the sources

- [x] 1.1 Move `Veriphy.lean`, `Veriphy/`, `VeriphyCheck.lean`, `VeriphyCheck/`, `VeriphyTest.lean`, `VeriphyTest/` and `assets/` under `lean/` with `git mv`, and add `srcDir = "lean"` to `lakefile.toml` (D1, D4). Verify with `lake build` (default targets), `lake build VeriphyAssets` and `lake build VeriphyTest.Kit VeriphyTest.Graph`, and with `git log --follow --oneline lean/Veriphy/Kit/Levels.lean` showing commits from before the move.
- [x] 1.2 Move `coverage/` to `lean/coverage/` and set its Veriphy requirement to `path = "../.."`, in the lakefile and the manifest (D3). Verify that both name `../..`, that it reaches the root lakefile, and that `lake build` at the root does not build `Coverage`. A full coverage run downloads Physlib and stays a manual step, as before.
- [x] 1.3 Delete the untracked `https:` directory at the root. Verify that `git status --short --ignored` no longer lists it.

## 2. Paths

- [x] 2.1 Update `scripts/bundle_check.py` and `scripts/sync_tables.sh`. Verify by running `python3 scripts/bundle_check.py <tmp>/VeriphyCheck.lean` and checking that the bundle builds with `lake env lean`, and by running `scripts/sync_tables.sh` with no change to the generated JSON.
- [x] 2.2 Update every document and docstring that names a moved path: the developer docs, the coverage and benchmark pages, the user guide, the recipes and the constitution, and name the module in the linear-algebra spec (D5). Verify with `git grep` that no tracked file outside `lean/`, the archive and the changelog names `Veriphy/`, `VeriphyCheck/`, `VeriphyTest/`, `assets/VeriphyAssets` or `coverage/` without the `lean/` prefix, and with `uv run nox -s docs -- build`.

## 3. Integration

- [ ] 3.1 Run the gate (checks, tests, the Sage-backed `lake build VeriphyTest`) and CI on the branch. Verify that every session and job is green.

## Workflow follow-up

- Archive the change. It ships with the next release, and needs none of its own.
