# Tasks

## 1. Records

- [x] 1.1 Add the record type, the canonical digest and the store to `veriphy.core` (D1, D2), with doctests. Verify with pytest: equal content under two paths gives one digest, a changed input gives another, a record is never overwritten, and a differing rerun keeps both.
- [x] 1.2 Add the step runner and the four kinds (D3), refusing a level on `agent` and `evidence` records. Verify with pytest on fake steps: replay returns the stored record without calling the step, `--rerun` calls it, and an evidence step that returns a level is rejected.

## 2. Steps

- [x] 2.1 Add `python -m veriphy` with `records` and the exit codes (D6). Verify with pytest on the command: `--json` prints only the record, and each status maps to its exit code.
- [x] 2.2 Add `validate`, `reason` and `report` over `veriphy.graph`, with `reason` pointing to its certificate (D5). Verify with pytest on the graph fixtures: each record matches the wrapped command's result, and a second `reason` starts no process.
- [x] 2.3 Add `elaborate` and `level` through `lake env lean` (D4). Verify with pytest on a small Lean workspace fixture, skipped without a Lean toolchain: a broken file is `refused` with its errors, and `level` matches `#veriphy_levels`.

## 3. Documents and integration

- [x] 3.1 Document the step command and the records in the user guide, and link the change from the architecture page. Verify with `uv run nox -s docs -- build`.
- [ ] 3.2 Run the gate (formatting of the changed files, checks, tests, docs) and CI. Verify that every session and job is green.

## Workflow follow-up

- Archive, and release with `meaning-step` or on its own as a minor version.
