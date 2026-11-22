# Proposal

## Why

Readers can't follow the documentation. The home page and the guide introduce packs, levels, trust classes,
primitives and the claim graph before they show what Veriphy does. No page shows every command, and some printed
output is stale: the documented `reproduce` output predates six-digit summaries and reported tolerances. Running every
command in order on one example also exposed rough edges in the CLI:

- `veriphy help` runs long step names into the next column.
- `agents list` shows the math pack's playbooks in a statistics workspace.
- `claims plan` reasons about the old graph with the `math` pack's levels.
- `workflow run` loops to its bound with no explanation when a step's record doesn't name the target.
- `claims clashes` prints "1 clashes".

## What Changes

- The documentation follows scikit-learn's structure:
  - a short home page;
  - an installation page;
  - a getting-started tour;
  - a tutorial that runs every command on one small example;
  - a user guide in numbered chapters;
  - a command reference generated from the CLI;
  - a configuration reference;
  - the pack pages.
- Every console session in the getting-started tour and the tutorial is run by the test suite against the real CLI, so
  the printed output can't go stale.
- A test checks that the tutorial uses every command of the CLI.
- The CLI fixes:
  - `veriphy help` sizes its columns to the longest name, and lists the Lean verbs only in a workspace that uses
    `math`.
  - `agents list` and `agents show` take `--pack`, as `agents path` does.
  - `claims plan` reasons about the old graph with the workspace's own packs.
  - `workflow run` says why it fails when a step's record doesn't name the target.
  - `claims clashes` writes "1 clash".

## Capabilities

### New Capabilities

- `distribution/documentation`: the documentation's structure, its executed examples, and its command coverage.

### Modified Capabilities

- `core/workflows`: `workflow run` refuses a target that a step's record doesn't name.
- `distribution/packaged-playbooks`: `agents list` and `agents show` take a pack.

## Impact

- The `docs/` pages, `properdocs.yml` and `README.md` change.
- New: `docs/generate_cli.py` and `tests/docs/test_console.py`.
- Code: `veriphy/__main__.py`, `agents/_cli.py`, `claims/_impact.py`, `claims/_checks.py` and `workflows/_engine.py`.
