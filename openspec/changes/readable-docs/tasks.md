## 1. CLI fixes

- [x] 1.1 `veriphy help`: columns sized to the longest name, Lean verbs only with `math`
- [x] 1.2 `agents list` and `agents show` take `--pack`
- [x] 1.3 `claims plan` reasons about the old graph with the workspace's packs
- [x] 1.4 `workflow run` explains a target that a step's record doesn't name
- [x] 1.5 `claims clashes` writes "1 clash"
- [x] 1.6 Tests for 1.1 to 1.5

## 2. Pages

- [x] 2.1 Rewrite README (home): what, one check, install, links
- [x] 2.2 New `overview/install.md`
- [x] 2.3 Rewrite `overview/getting_started.md` as a tour of short, runnable sections
- [x] 2.4 New `overview/tutorial.md`: every command on the example study
- [x] 2.5 Rewrite `overview/user_guide.md` in numbered chapters, plain words
- [x] 2.6 `docs/generate_cli.py` writes `overview/commands.md`; `overview/reference.md` becomes the configuration reference
- [x] 2.7 Update `properdocs.yml` nav, `packs/index.md` links, and pages that link to moved sections
- [x] 2.8 Refresh stale outputs on the pack pages

## 3. Tests

- [x] 3.1 `tests/docs/test_console.py` runs the console sessions of the tour, the tutorial, the user guide and the pack pages
- [x] 3.2 Coverage test: every CLI command appears in the tutorial or on the math page

## 4. Gate

- [ ] 4.1 `nox -s checks`, the docs build, and the full test suite pass
- [ ] 4.2 CI is green
