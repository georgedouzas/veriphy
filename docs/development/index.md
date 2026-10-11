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

## Adding a certificate

| stage | what | where |
|---|---|---|
| 1. parse | goal + context → `Problem` (shared atom table, `=`/`≤`/`<`/`≠`, `∃` binders, conjuncts; inaccessible hypotheses skipped) | `withProblem` (`Kit/Problem.lean`) |
| 2. request | typed daemon call, refused during replay | `Kit.run (Bridge.…)` / `Bridge.call` (`Kit/Replay.lean`, `Bridge.lean`) |
| 3. solve | the certificate search, the only new code | a method in `src/veriphy/oracle/` registered with `@_register_method(TABLE, "name", vars=_coerce_ring, poly=_coerce_poly, …)`, plus `solve_exact_lp` |
| 4. rebuild | rationals, polynomials, weighted hypothesis sums, witnesses, step blocks, all unhygienic | `Kit/Build.lean` |
| 5. check | pick a family | `Checker.*` (`Kit/Family.lean`) |
| 6. emit | run exactly what is printed, replay it if `veriphy.checkReplay`, emit one `Try this:` | `closeAndEmit` |

A complete tactic (`∃ x, p x = 0` by a rational root):

```lean
elab ref:"my_root" : tactic => do
  -- stages 1–4: extract, call Sage, rebuild — inside the problem's context
  let root ← withProblem { tac := "my_root", allowExists := true } fun p => do
    let .exists_ _ #[c] := p.goal | throwError "my_root: expected `∃ x, p x = q x`"
    let some r := (← Kit.run "roots" (Bridge.roots c.poly "x0")).head?
      | throwError "my_root: no rational root"
    return r
  -- stages 5–6: the witness family builds the proof; closeAndEmit runs it, replays it, emits it
  closeAndEmit ref (← Checker.witness [root] 1)
```

Tests run with `set_option veriphy.checkReplay true`: every emitted replacement is
pretty-printed, re-parsed and re-run on the original goal with the bridge
disabled. That catches hygienic names (`h✝`), printer round-trip failures and
hidden Sage calls. Daemon methods are tested with `uv run nox -s tests` (pytest
and doctests on SageMath's interpreter), and the kit itself (Sage-free) with
`lake build VeriphyTest.Kit`.

## Known future work

- Persistent daemon (each tactic call currently pays ~2 s of Sage startup).
- A daemon that installs without SageMath, through the modular
  [passagemath](https://github.com/passagemath/passagemath) wheels, once they
  are shown to cover every method (Singular `lift`, the PPL LP backend,
  symbolic sums and simplification).
- `sage_sos` beyond completed squares and hinted squares (exact rational SDP).
- Candidate upstreaming of checkers to LeanSage.
