# Design

## Context

The motivation is in proposal.md (Why). The current state below shapes the approach.

- **Lean (~600 lines).**
  - `Veriphy/Translate.lean` holds `exprToSage` (translation with an atom table in `StateRefT (Array Expr) MetaM`) and the builders `ratStx`, `termStx` and `polyStx`.
  - `Veriphy/Bridge.lean` spawns `sage -python server.py` once per request. Each method hand-writes its JSON encoding and decoding.
  - Seven tactics in `Veriphy/Tactic/` each re-implement some of the following: atom-table threading through an `IO.Ref`, hypothesis scanning of the local context, relation classification (three separate copies), `Try this:` emission, and hygiene workarounds.
- **The copies have drifted.** `sage_farkas` skips `hasMacroScopes` hypotheses but `sage_lincomb` does not.
- **Run versus print.** `sage_factor` runs `ring1` on an `Expr` goal it built itself, then prints a different syntax tree. What it runs and what it prints are not the same object, which is exactly how print-only bugs slip through.
- **Python.** `sage_bridge/server.py` (~530 lines) dispatches through a dict. Validation (`_ring`) is applied by hand in some methods and not others. Three methods build PPL LPs inline, each with its own try/except. `run_script` already has the exec, preparse, stdout-capture and timeout machinery that `certify` needs.
- **mathlib `linear_combination`** (pinned at v4.34.1) supports `≤`/`<` goals. It proves multiplier nonnegativity with `positivity` and closes with `Ring.proveLE`/`proveLT`, which accept a constant nonnegative slack. The inequality family can therefore close `a ≤ b` goals directly and needs the `have κ … ; norm_num` route only for `False`.
- **Constraint.** The trust base must not grow: only mathlib checkers close goals (DESIGN.md §2).

## Goals / Non-Goals

**Goals:**
- A tactic author writes stage 3 (a Sage method) and picks a family. Everything else comes from the kit. As a rough check, each refactored tactic file should be under about 40 lines.
- Each hygiene, empty-LP or relation-classification fix is made in exactly one place.
- The agent can certify one-off identities, inequalities and witnesses without a new tactic.

**Non-Goals:**
- A persistent daemon. Each call still spawns Sage; this is still future work in DESIGN.md §8.
- New Sage solving power, such as full SOS by exact SDP. `certify` only exposes what a script can compute.
- `sage_certify` support for the `sum` and `cases` families. `sum` already needs no oracle (`#sage_sum` plus `sage_sum n`), and `cases` is plain `decide`. Both are kit families for tactic authors only.
- Script files on disk for `sage_certify`. The script is a string literal; it never reaches committed proofs, so ergonomics matter less than for proof text.
- Upstreaming to LeanSage or mathlib.

## Decisions

### D1. Module layout: `Veriphy/Kit/`

- `Kit/Problem.lean` holds the problem types, `ProblemM` (the atom-table monad) and the extractors. It imports `Translate` for `exprToSage`.
- `Kit/Build.lean` holds the builders: `ratStx`, `termStx` and `polyStx` (moved from Translate), plus `weightedSum`, `witness`, `steps` and `freshIdent`.
- `Kit/Family.lean` holds the checker families and `closeAndEmit`.
- `Kit/Replay.lean` holds the `veriphy.checkReplay` option and the replay procedure. It is imported by Family.
- `Kit.lean` re-exports the four modules.

The builders keep their names in `namespace Veriphy` and `Translate` imports `Kit/Build`, so existing references keep compiling. *Alternative:* a single `Kit.lean` file. Rejected because it would grow past readability and mixes meta-level parsing with syntax building.

### D2. The atom table is a monad, not an `IO.Ref`

`abbrev ProblemM := StateRefT (Array Expr) MetaM`, with `tryTranslate : ProblemM α → ProblemM (Option α)`. `tryTranslate` saves the atom table and rolls it back on failure. This replaces the duplicated `atomsRef`/`runTr`/`saved` blocks. `extract (ref) (opts) : TacticM Problem` runs the whole thing inside `withMainContext`, and options select what to collect (goal kind, relations allowed in hypotheses).

### D3. The problem data model

The model is a `Constraint` with fields `lhs rhs : Expr`, `rel : Rel` (`eq | le | lt | ne`), `poly : String` (the Sage form of `lhs - rhs` after flips) and `src : Option Name`. A `Problem` holds:
- `carrier : Expr`
- `atoms : Array Expr`
- `hyps : Array Constraint`
- `goal : Goal`, where `Goal` is one of `rel Constraint | falsum | exists (binders : Array Expr) (body : Array Constraint)`.

`Problem.toJson` produces the serialization in the problem-extraction spec. Atom Lean renderings are produced with `ppExpr`, for script readability only. The single `Rel` type and `relOf?` replace the three classification copies.

### D4. "Run what you print"

Every family builds one `TSyntax tactic`, runs exactly that syntax with `evalTactic`, and emits the same object through `addSuggestion`. `sage_factor` changes from assigning `Eq.trans` with an internally checked `ring1` to running its printed `refine Eq.trans (show … by ring1) ?_`. The cost is one extra elaboration of the `show`. The benefit is that the run-versus-print bug class goes away. *Alternative:* keep the Expr-level checks and rely on replay alone. Rejected: replay is opt-in, and running the printed syntax is free correctness.

### D5. Hygiene rules, enforced in the builders

- No bare identifier ever appears inside a `` `(…) `` quotation in tactic code. Lemma and hypothesis references are spliced in as `mkIdent` values (`mkIdent ``not_le`), and quotations contain only syntax keywords.
- Fresh local names come from `freshIdent (base : Name)`, which picks an unused user name in the current local context (`hfarkas`, then `hfarkas_1`, …).
- The extractor never collects inaccessible hypotheses, so every `src` name is printable.

Replay (D6) is the backstop that catches anything these rules miss.

### D6. Replay mechanics

`closeAndEmit` works in these steps:
1. Save the state `s₀`.
2. Run the proof and record the resulting goals `G`.
3. If `veriphy.checkReplay` is on:
   - print the proof with `PrettyPrinter.ppTactic`;
   - parse the string with `Parser.runParserCategory env `tactic`;
   - save `s₁`, restore `s₀`, and run the parsed tactic under `withOptions (veriphy.internal.replaying := true)`;
   - compare the resulting goals with `G` (same count, types defeq after `instantiateMVars`);
   - restore `s₁`.
4. Add the suggestion.

The bridge is disabled through that internal option. The kit's single entry point `Kit.call` (a `CoreM` wrapper around `Bridge.request`) throws when the option is set. *Alternative:* a global `IO.Ref` flag set with `initialize`. Rejected because `initialize` in an interpreted, non-precompiled library is fragile, while options are scoped and restored automatically. Direct `Bridge.*` calls from tactics are disallowed by convention, and a task greps for them.

### D7. Typed bridge calls

`Bridge.call (method) (params : Json) (decode : Json → Except String α) : IO α` replaces the decode boilerplate. The existing `Bridge.factor`, `sos` and the rest become one-liners over it, keeping their signatures for `#sage_factor`/`#sage_sum`. `Kit.call` lifts `Bridge.call` into `CoreM` and adds the replay guard.

### D8. Python method framework

```python
@method("farkas", vars=Vars, polys=PolyList, rels=RelList)
def farkas(R, polys, rels): ...
```

- The decorator registers the method in `METHODS` and takes an `advisory=` flag.
- It coerces parameters in declaration order. `Vars` builds `R` and validates identifiers. `Poly`/`PolyList` parse in `R`. Each coercer raises `ParamError(param, why)`.
- It encodes the return value with `encode()`: `QQ`/`Integer` become strings, polynomials become term lists, tuples become lists, and dicts are encoded recursively. For non-advisory methods it rejects floats.
- It wraps every exception as `"<method>: <reason>"`.

`main()` is unchanged apart from producing the unknown-method message.

`exact_lp(nvars, eqs, les, objective, nonneg)` returns `list[QQ] | None`:
- zero variables gives `[]`, and zero constraints gives the zero vector, both without touching PPL;
- otherwise it builds a PPL `MixedIntegerLinearProgram`, mapping `MIPSolverException` to `None`.

`sos` hints, `farkas` and `exists` migrate onto it. *Alternative:* `Polyhedron`-based feasibility. Rejected because the existing code is PPL-based and already exact.

### D9. `certify` reuses `run_script`'s engine

The exec, preparse, stdout-capture and SIGALRM code is factored into `_run_sage(script, ns, timeout) -> (ns, stdout)`. `certify` pre-binds `R`, the generators `x0…`, `hyps` (a list of `Hyp(name, poly, rel)` namedtuples), `goal` (`Hyp` or `None`), `binders` and `atoms` (name to Lean text), then runs the script. It reads `ns["certificate"]` and validates it against the family schema:
- `identity`: `{"cofactors": {name: poly}}`.
- `inequality`: `{"weights": {name: QQ≥0}, "squares": [(QQ≥0, poly)]}`. Weights on `eq` hypotheses may be any rational polynomial.
- `witness`: a list of QQ.

Shorthand forms (a bare dict of weights, a bare list) are normalized. The method returns exact encodings, and any error includes the truncated stdout. Lean re-validates arity and names; Python validation exists only to give good errors.

### D10. `sage_certify` syntax and family dispatch

```lean
syntax "sage_certify " ("identity" <|> "inequality" <|> "witness") str : tactic
```

Using keywords rather than an ident makes an unknown family a parse error, which satisfies "rejected at elaboration time". The tactic:
1. maps the family to its extraction options and checks the goal shape before calling Sage;
2. runs `Kit.call "certify"`;
3. builds the proof with the D1 builders and calls the family's `close` through `closeAndEmit`.

Inequality reconstruction:
- **`≤`/`<` goal:** `linear_combination Σ wᵢ * hᵢ + Σ cⱼ * sq_nonneg (qⱼ)`.
- **`False` goal:** `have hκ : (κ : α) ≤ 0 := by linear_combination …` (or `< 0`), then `norm_num at hκ`, as `sage_farkas` does today.

### D11. Mapping the existing tactics onto families

| tactic | extraction | Sage | family |
|---|---|---|---|
| `sage_factor` | goal `=` (lhs only) | `factor` | identity (`ring1` rewrite, residual goal) |
| `sage_sos [hints]` | goal `0 ≤ p` | `sos` | inequality (Σ c·sq_nonneg, via `le_of_le_of_eq … ring1` or `linear_combination`) |
| `sage_lincomb` | goal `=`, eq hyps | `lincomb` | identity (`linear_combination`) |
| `sage_witness` | `∃` one binder, one `=` | `roots` | witness |
| `sage_exists` | `∃` binders, conjuncts | `exists` | witness |
| `sage_farkas` | goal ≤/</False, hyps eq/le/lt | `farkas` | inequality (refutation) |
| `sage_sum` | none | none | sum (macro unchanged in behavior) |

`sage_sos` keeps its current printed form if switching to `linear_combination` changes which goals close. The spec requires preserving behavior, not identical text.

### D12. Tests

- `VeriphyTest.lean` turns on `set_option veriphy.checkReplay true` at the top and adds these regressions:
  - `sage_farkas` on `u ≤ 0`, the negation step;
  - an inaccessible hypothesis (`intro` of an unnamed hypothesis, then `sage_lincomb`);
  - an empty LP (`sage_exists` on `∃ x y : ℚ, x = y`, and `sage_farkas` with only equality hypotheses);
  - `sage_certify` for each of its three families, with a negative example via `fail_if_success`.
- `sage_bridge/test_server.py` uses `unittest` and calls the decorated functions directly. It covers parameter errors, exact encoding, the `exact_lp` empty and infeasible cases, `certify` schema errors and ping compatibility. Run it with `sage -python -m unittest sage_bridge/test_server.py`.

## Risks / Trade-offs

- **[Risk]** Pretty-printed tactic syntax may not round-trip for reasons unrelated to hygiene, such as notation and coercion arrows (`↑n`) or `open` scoping. → Mitigation: replay errors print the text, which makes failures diagnosable. Builders emit explicit type ascriptions (`(κ : α)`) where coercions matter. Lemma idents use the shortest name that resolves under the current opens; if that proves flaky, fully qualified names are used.
- **[Risk]** Under "run what you print", `sage_factor` elaborates its `show` term with `elabTermEnsuringType` semantics, which could differ from the current `Expr` path on implicit coercions. → Mitigation: the existing tests cover ℚ and ℝ; add an `f a` atom case (already present).
- **[Risk]** `sage_certify` scripts execute arbitrary Sage code. → This is the same accepted boundary as `run_script` (server docstring): the daemon is a user-launched, untrusted oracle, and only the kernel is trusted.
- **[Trade-off]** Replay roughly doubles elaboration time per call when it is on. It is opt-in and enabled only in tests.
- **[Trade-off]** The fixed family set means a new proof shape, such as a determinant certificate, still needs kit work. That is intentional: DESIGN.md §4 says the catalog grows only on demand, and a family is the unit of that growth.
- **[Risk]** Refactoring seven tactics at once could regress one silently. → Mitigation: migrate one tactic per task and run `lake build VeriphyTest` after each, with replay on from the first migration.

## Migration Plan

The work is internal and lands in one branch:
1. Build the kit, the bridge `call` and the Python framework.
2. Migrate the tactics one by one.
3. Add `sage_certify`.
4. Update the docs.

Rollback is a plain revert, because there is no persisted data and no tactic syntax change. Committed downstream proofs are unaffected: they contain only mathlib tactics.

## Open Questions

Both were settled during implementation:

- `sage_sos` keeps printing `le_of_le_of_eq (by positivity) (show … by ring1)` (`Checker.squares`). It already covers the degenerate cases (`p = 0`, constant-only decompositions) that a `linear_combination` form would need special-casing for, and existing output is preserved.
- The `certify` script timeout reuses `run_script`'s 120 s default (`timeout_s`).

Also found during implementation: suggestions were attached to the tactic keyword only, so applying the suggestion for `sage_sum n`, `sage_sos [hints]` or `sage_certify … "…"` left the arguments behind. `closeAndEmit` now attaches the suggestion to the whole tactic (`getRef`).
