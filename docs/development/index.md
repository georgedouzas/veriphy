# Development

## Environment setup

This project uses [uv](https://github.com/astral-sh/uv) to manage the various dependencies. To setup the development
environment you can follow the next steps:

- Install [uv](https://github.com/astral-sh/uv).

- Fork and clone the repository.

- `uv sync` from the root of the project to install the main and development dependencies.

- Install the Sage session from the checkout into SageMath with `sage -pip install -e .`, so the tactics use the working
  tree's Sage session. Point `VERIPHY_SAGE_SESSION` at `src/veriphy/packs/math/primitives/sage/__main__.py` to try Sage session changes without
  reinstalling.

- `cd src/veriphy/packs/math/lean && lake exe cache get && lake build` to build the Lean library.

## Running the checks

- `uv run nox -s checks` runs ruff, mypy, bandit, the docstring checks and the dependency audit.
- `uv run nox -s tests` runs pytest and the doctests on SageMath's interpreter.
- In `src/veriphy/packs/math/lean/`, `lake build VeriphyTest` runs the tactic suite against live Sage, with replay
  on, `lake build VeriphyTest.Kit` runs the kit tests, which need no Sage, and `lake build VeriphyCheck` builds the
  checkers; `src/veriphy/packs/math/lean/VeriphyTest/Check.lean` tests them without Sage.

## How the pieces fit

| Stage | Where |
|---|---|
| Extract the goal and every nameable hypothesis (polynomial forms where they exist, Lean text always) | `withLenientProblem`, `src/veriphy/packs/math/lean/Veriphy/Kit/Problem.lean` |
| Send the problem and the script to the Sage session (one Sage process per Lean process) | `Kit.run (Bridge.run …)`, `src/veriphy/packs/math/lean/Veriphy/Bridge.lean` |
| Run the script with `problem` and the toolkit bound; read the `found(...)` it returns | `run`, `src/veriphy/packs/math/primitives/sage/methods/_scripts.py` |
| Parse the block, run exactly that, reject `sorry` and non-standard axioms, replay, emit | `veriphy certify`, `closeAndEmit` in `src/veriphy/packs/math/lean/Veriphy/Kit/Family.lean` |

## Layout

```text
src/veriphy/                  the Python package: the layers, and the packs
src/veriphy/packs/core/       the framework pack: the built-ins every workspace has
src/veriphy/packs/math/       the math pack
  lean/                       its Lean library, with lakefile.toml, lean-toolchain and lake-manifest.json
    Veriphy/                  veriphy certify, problem extraction, checks and replay, the Sage session bridge
    VeriphyCheck/             mathlib-only kernel checkers, bundled by nox -s bundle
    VeriphyTest/              Lean tests: the kit (no Sage), veriphy certify examples, the benchmark
    assets/                   recipe assets projects copy into .veriphy/lean/
    coverage/                 a Lake project measuring translation coverage on Physlib and mathlib
    .veriphy/certificates/    the certificate scripts the Lean tests run
  agents/                     playbooks, recipes with templates, and the skills
src/veriphy/packs/<pack>/      the field packs (statistics, physics, …) and subfield packs (genomics, …)
docs/examples/                the packs' worked examples, run by the tests
tests/                        Python tests
```

The repository is generated from [copier-modern-python](https://github.com/georgedouzas/copier-modern-python), and
`copier update` pulls template changes. The Python code follows `openspec/constitution.md`.

## Sage session protocol

Lean keeps one Sage session per file it compiles. It reads one JSON-RPC 2.0 request per line on stdin and writes one
response per line on stdout. From Python, a primitive calls one method per process instead:
`sage -python -m veriphy.packs.math.primitives.sage call <method> <input> <out>`. The methods are `ping`, `run` (a proof script against a serialized problem) and the advisory
`symbolic_check`, `matrix_check`, `solve` and `run_script`.

Scripts run with the Sage session's own privileges. The Sage session is a user-launched, untrusted oracle, and the trust boundary
is the Lean kernel.

## Adding a recipe

A recipe is knowledge, not code in Veriphy.

1. Write `src/veriphy/packs/math/agents/recipes/templates/<name>.sage` with the catalog header (`name`, `technique`, `goal`,
   `description`). Make it generic: it reads `problem`, and marks the lines a user adapts with `EDIT`.
2. Write `src/veriphy/packs/math/agents/recipes/<name>.md`, embedding the template verbatim and giving its decision rule, a
   worked example and its failure modes.
3. Add a Lean example that runs the template with `veriphy certify "src/veriphy/packs/math/agents/recipes/templates/<name>.sage"`
   (`src/veriphy/packs/math/lean/VeriphyTest/SageRun.lean`, or the benchmark if it replaces a former tactic).
4. Add it to the index in `src/veriphy/packs/math/agents/prove.md` step 3c.

`tests/recipes/test_templates.py` checks that each recipe embeds its template, that the header is complete, and that
every template runs in the Lean tests.

## Adding a toolkit building block

Add to `veriphy.packs.math.script` only what is general and hard to get right in a few lines at proof time: an emitter that
writes a Lean construct correctly, or an exact solver. Technique-specific search (Farkas rows, ideal lifts, product
search) belongs in a recipe template. Each public toolkit function needs a docstring with a runnable example, a test,
and for emitters a case in the Lean parse check (`tests/toolkit/conftest.py`).

The toolkit is organized by **certificate shape**, not by mathematical definition. There are far more definitions
than any toolkit could cover, but few ways for an untrusted computation to hand Lean something it can check cheaply:
a linear combination of hypotheses, a sum of squares, a witness, a factorization, a chain of derivative lemmas, a
substitution, a list a kernel checker reads. A module such as `_sos` exists because "a sum of squares plus a
positive combination" is one such shape that many problems reduce to. A new mathematical area earns a module when it
brings a new shape, or when emitting an existing shape for it is hard to get right (`_ode` reuses `_derivative`'s
chains; `_reflect` packs data for the `VeriphyCheck` checkers). Otherwise it is a recipe.

## Adding a core translation entry

The core table (`mathlib` namespace) is `coreTable` in `src/veriphy/packs/math/lean/Veriphy/Kit/Table.lean`; the Python toolkit reads a JSON
copy.

1. Add the function, constant, coercion or rewrite entry, with its domain conditions and an example.
2. Run `nox -s tables` to regenerate `src/veriphy/packs/math/script/core_table.json` and the pack copies. A
   Sage-free kit test fails until the copies match.
3. Add a kit test in `src/veriphy/packs/math/lean/VeriphyTest/Kit.lean` showing the translation and its conditions, and a round trip in
   `src/veriphy/packs/math/lean/VeriphyTest/SageRun.lean` if Sage's name differs from the obvious one.
4. Rerun the coverage runner (`docs/development/coverage.md`) when the entry targets a frequent opaque head.

## Adding a library pack

A pack holds one library's translation entries, notations and sign conventions, in its own namespace. It is active
only when the library is imported. Veriphy never imports the library: constants are named as strings and checked when
the pack activates.

1. Write `src/veriphy/packs/math/lean/Veriphy/Packs/<Library>.lean` with a `Pack`: the library name, a sentinel constant whose presence means
   the library is imported, and the table. Record sign conventions (metric signature, normalizations) under
   `conventions`, because scripts read them to state results in the library's own terms.
2. Add it to `shippedPacks` in `src/veriphy/packs/math/lean/Veriphy/Kit/Packs.lean` and run `nox -s tables`.
3. Test activation and translation in the coverage runner (`src/veriphy/packs/math/lean/coverage/PackCheck.lean`), which imports the library.
   Library recipes go in `src/veriphy/packs/math/agents/recipes/<library>/`.

## Adding a checker

Checkers live in `src/veriphy/packs/math/lean/VeriphyCheck/` and import only mathlib, so `nox -s bundle` can bundle them for projects
that do not depend on Veriphy.

1. Write a `Bool`-valued function computed by structural recursion over lists or `List.finRange` (no well-founded
   recursion, which the kernel does not unfold efficiently), and a soundness theorem from `= true` to the mathlib
   statement.
2. Test it in `src/veriphy/packs/math/lean/VeriphyTest/Check.lean` on a small true case, a false case the kernel refuses, a large case, and
   `#print axioms` showing only `propext`, `Classical.choice` and `Quot.sound`.
3. Add the emitter in `src/veriphy/packs/math/script/_reflect.py`, deciding by size between an entrywise proof and the
   checker. Measure before adding: a kernel checker that is slower than mathlib's tactic on realistic inputs (as a
   polynomial normalizer is against `ring`) does not belong.

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
failures and hidden Sage calls. `lake build VeriphyTest.Kit`, in the math pack's `lean/`, covers extraction, `closeAndEmit` and the axiom guard
without Sage. `src/veriphy/packs/math/lean/VeriphyTest/SageRun.lean` and `src/veriphy/packs/math/lean/VeriphyTest/Benchmark.lean` need Sage.

## Releases

Each release is one git tag `X.Y.Z`, and that tag is the only place a version is written.

| Channel | Artifact | How a user gets it |
|---|---|---|
| Lake | the Lean library | `[[require]] … rev = "X.Y.Z"`, `subDir = "src/veriphy/packs/math/lean"` |
| PyPI | the `veriphy` package, including the Sage session | `sage -pip install veriphy` |
| Claude plugin | the skills and playbooks | `claude plugin install veriphy@veriphy` |

CI gates a release with a Lean job without Sage, the Python checks, and an integration job in a SageMath container that
installs the built wheel and runs the tactic suite with replay on.

## Known future work

- A Sage session that installs without SageMath, through the modular
  [passagemath](https://github.com/passagemath/passagemath) wheels, once they are shown to cover what scripts need.
- Exact SOS on the boundary of the PSD cone (facial reduction). Today that case needs hinted squares.
- A separate repository of shared, curated certificate scripts.
