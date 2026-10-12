# Development

## Environment setup

This project uses [uv](https://github.com/astral-sh/uv) to manage the various dependencies. To setup the development
environment you can follow the next steps:

- Install [uv](https://github.com/astral-sh/uv).

- Fork and clone the repository.

- `uv sync` from the root of the project to install the main and development dependencies.

- Install the Sage daemon from the checkout into SageMath with `sage -pip install -e .`, so the tactics use the working
  tree's daemon. Point `VERIPHY_SAGE_SERVER` at `src/veriphy/sage_server/__main__.py` to try daemon changes without
  reinstalling.

- `lake exe cache get && lake build` to build the Lean library.

## Running the checks

- `uv run nox -s checks` runs ruff, mypy, bandit, the docstring checks and the dependency audit.
- `uv run nox -s tests` runs pytest and the doctests on SageMath's interpreter.
- `lake build VeriphyTest` runs the tactic suite against live Sage, with replay on.
- `lake build VeriphyTest.Kit` runs the kit tests, which need no Sage.

## How the pieces fit

| Stage | Where |
|---|---|
| Extract the goal and every nameable hypothesis (polynomial forms where they exist, Lean text always) | `withLenientProblem`, `Veriphy/Kit/Problem.lean` |
| Send the problem and the script to the daemon session (one Sage process per Lean process) | `Kit.run (Bridge.run …)`, `Veriphy/Bridge.lean` |
| Run the script with `problem` and the toolkit bound; read `proof` | `run`, `src/veriphy/oracle/_scripts.py` |
| Parse the block, run exactly that, reject `sorry` and non-standard axioms, replay, emit | `sage_run`, `closeAndEmit` in `Veriphy/Kit/Family.lean` |

## Adding a recipe

A recipe is knowledge, not code in Veriphy.

1. Write `prompts/recipes/templates/<name>.sage` with the catalog header (`name`, `technique`, `goal`,
   `description`). Make it generic: it reads `problem`, and marks the lines a user adapts with `EDIT`.
2. Write `prompts/recipes/<name>.md`, embedding the template verbatim and giving its decision rule, a worked example
   and its failure modes.
3. Add a Lean example that runs the template with `sage_run file "prompts/recipes/templates/<name>.sage"`
   (`VeriphyTest/SageRun.lean`, or the benchmark if it replaces a former tactic).
4. Add it to the index in `prompts/prove.md` step 3c.

`tests/recipes/test_templates.py` checks that each recipe embeds its template, that the header is complete, and that
every template runs in the Lean tests.

## Adding a toolkit building block

Add to `veriphy.toolkit` only what is general and hard to get right in a few lines at proof time: an emitter that
writes a Lean construct correctly, or an exact solver. Technique-specific search (Farkas rows, ideal lifts, product
search) belongs in a recipe template. Each public toolkit function needs a docstring with a runnable example, a test,
and for emitters a case in the Lean parse check (`tests/toolkit/conftest.py`).

## Migrating from the removed tactics

| Removed | Use |
|---|---|
| `sage_factor` | `factor_rewrite` |
| `sage_sos`, `sage_sos [hints]` | `sos` (put hints in `HINTS`) |
| `sage_lincomb`, `sage_certify identity` | `ideal_membership` |
| `sage_witness`, `sage_exists`, `sage_certify witness` | `witness` |
| `sage_sum n`, `#sage_sum` | `sum_induction` (find the closed form with Sage's `sum`) |
| `sage_farkas`, `sage_certify inequality` | `farkas` (or `sos`/`hint_search` for squares) |

Committed proofs need no migration, because they contain only emitted replacements.

## Testing

Tests run with `set_option veriphy.checkReplay true`: every emitted replacement is pretty-printed, re-parsed and
re-run on the original goal with the bridge disabled. That catches hygienic names (`h✝`), printer round-trip
failures and hidden Sage calls. `lake build VeriphyTest.Kit` covers extraction, `closeAndEmit` and the axiom guard
without Sage. `VeriphyTest/SageRun.lean` and `VeriphyTest/Benchmark.lean` need Sage.

## Known future work

- Broader translation, specified in the `symbolic-translation` change: rational functions, transcendental functions,
  matrices and casts as Sage symbolic expressions, with domain conditions.
- A daemon that installs without SageMath, through the modular
  [passagemath](https://github.com/passagemath/passagemath) wheels, once they are shown to cover what scripts need.
- Exact SOS on the boundary of the PSD cone (facial reduction). Today that case needs hinted squares.
- A separate repository of shared, curated certificate scripts.
