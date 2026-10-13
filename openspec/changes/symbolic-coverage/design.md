# Design

## Context

The symbolic translation (`Veriphy/Kit/Symbolic.lean`) maps Lean terms to a small IR (`SymExpr`) through hard-coded tables, and records domain conditions as `(term, ne | nonneg | pos)`. `Problem.enrich` runs it over every hypothesis and the goal. The Python toolkit parses the serialized forms into Sage's symbolic ring (`parse_symbolic`) and renders results back with a function table in `_symbolic_emit.py`. Rendering is untyped: a term is printed and Lean elaborates it with whatever type unification finds. The `transcendental_rewrite` template keeps its own lemma table.

Physlib (commit `ee0bfb40`, the GUT branch) and Veriphy both pin mathlib `v4.34.1`, and mathlib declares an `Archive` library target, so one Lake project can import Veriphy, Physlib and `Archive` together.

## Goals / Non-Goals

**Goals:**
- One table format that serves the core entries and the project entries, in both directions.
- A semantic gap is either bridged by a domain condition or the term stays opaque, so Sage never simplifies a term whose Lean meaning differs.
- A coverage number that is reproducible from pinned revisions.

**Non-Goals:**
- Complex branch cuts beyond the existing `Complex` table (`Complex.log`, `Complex.arg` stay text-only).
- Integrals and limits as translated constructs. Series appear only inside certified numerics, as truncations with explicit remainders.
- Abstract category theory (universal properties, limits, adjunctions). Mathlib's automation owns it. Veriphy covers categories only through explicit finite data: fusion categories and linear natural transformations.
- Abstract manifolds. The geometry component works in coordinates, against reference definitions, until mathlib or Physlib provides coordinate expressions to state against.
- Running the coverage measurement in CI, since it needs a Physlib build.

## Decisions

### D1. Tables as data, one schema

Every function and rewrite entry, core or project, is a record with these fields:

```text
lean, arity, sage, applies_to (argument types), result type,
conditions [(argument index or pair, kind)], round_trip example
```

Rewrite entries carry `lemma`, `functions`, `reverse`, `side` and `example`. The core tables become a Lean array of such records, plus a mirrored JSON file shipped in the Python package (`veriphy/toolkit/core_table.json`). A Sage-free Lean test checks that the two agree. Project entries are JSON under `.veriphy/translations/`.

**Alternatives considered:**
- Code per entry, as now. It cannot be extended without a release.
- Lean attributes in the project, such as `@[veriphy_sage "cosh"]`. That would need the project to import a Veriphy elaborator into its own sources, and the daemon would still need the table. JSON is readable from both sides and reviewable as data.

### D2. Extensions travel with the problem

At extraction time, Lean loads `.veriphy/translations/*.json` from the workspace root and validates each file (field names, arity, condition kinds, Lean constant exists in the environment). It merges the project entries after the core entries, rejects conflicts, and serializes the merged project entries in the problem (`"extensions"`). Python renders from core plus `problem.extensions`, so both directions use one table per call. The loaded tables are cached per Lean process, keyed by the files' modification times.

### D3. Conditions generalize to a proposition shape

`DomainKind` gains `le`, with two terms. Conditions on entries are written as `{"kind": "le", "args": [0, 1]}` or `{"kind": "pos", "arg": 0}`, plus constants (`{"kind": "le", "lhs": "-1", "arg": 0}` for `arcsin`). The discharge search accepts the hypothesis forms already accepted, plus `b ≤ a` derived from `b < a`.

### D4. Semantic gaps decided at translation

Each gap is decided where the term is translated:
- **ℕ subtraction:** translated to `a - b` only when a hypothesis discharges `b ≤ a`. Otherwise the term stays an atom.
- **ℕ/ℤ `/` and `%`:** translated to `floor(a/b)` and `mod(a, b)` when `b` is a positive numeral, or a hypothesis gives `0 < b`. Otherwise atom.
- **`Real.arcsin`/`arccos`:** translated with conditions `-1 ≤ x` and `x ≤ 1` (Lean clamps outside the interval).
- **`rpow`:** translated with `0 < x`, or `0 ≤ x` when the exponent is a positive numeral.
- **`deriv`:** translated as `diff(body, k).subs(k == point)` only when the body is fully in coverage. Conditions are collected for the body, then substituted at the point.

### D5. Typed sub-expressions

`SymExpr` gains `typed (ty : String) (e : SymExpr)`, emitted wherever the Lean type changes: a cast from ℕ or ℤ into a field, `Int.floor`, `Int.ceil`, and ℕ/ℤ arithmetic under a field. It serializes as `typed(e, 'ℕ')`.

In Python, `parse_symbolic` evaluates `typed` as the identity, so Sage simplifies freely, and records each marked sub-expression with its type in `problem.typed`. The renderer types a sub-expression in three ways:
- **Integer-valued operators** (`factorial`, `binomial`, `gcd`, `mod`, `floor`, `ceil`, integer division) are typed by rule. They render at ℕ when all their atoms are ℕ, at ℤ otherwise, and are cast to the enclosing type.
- **Recorded sub-expressions** that still occur verbatim render with their recorded type and a cast.
- **Everything else** renders at the expected type, which is the carrier unless the script names one. The outermost term is ascribed.

When Sage has simplified a recorded sub-expression away, its cast is lost and Lean elaborates by unification. The kernel checks the result either way.

**Alternatives considered:**
- Inferring every type in Python from the atom types. That cannot see that `n % 7` is computed in ℕ inside a real expression.
- A formal Sage function for the marker. That would block the simplifications scripts rely on.

### D6. Derivatives by structural `HasDerivAt`

`has_deriv_at(expr, var, point, problem)` walks the Sage expression and composes mathlib terms:
- `hasDerivAt_id`, `hasDerivAt_const`;
- `.add`, `.sub`, `.mul`, `.div` (needs a denominator `≠ 0`), `.pow`;
- `Real.hasDerivAt_exp`, `.log` (needs `≠ 0`), `.sqrt` (needs `≠ 0`), `Real.hasDerivAt_sin`/`cos`;
- `.rpow_const`, through the `.comp` forms.

The `derivative` recipe closes `deriv f a = v` with `rw [(term).deriv]` followed by `ring_nf` or `field_simp; ring`. Sage's derivative supplies `v` and the lie detection.

**Alternative considered:** `simp` with derivative lemmas. It handles simple cases, but fails silently on compositions, and gives no structure to report a missing condition.

### D7. Coverage measurement

`#veriphy_coverage [Prefix, …]` (writing its report to `.veriphy/coverage/<name>.json` unless a path is given) iterates the environment's constants whose module starts with a prefix, keeping theorems only. For each, it runs `forallTelescopeReducing` on the type, collects relations from hypothesis types and the conclusion, and runs the symbolic pass (with the project's tables). It classifies atoms by `getAppFn`: an fvar head is uninterpreted, a const head is opaque. It aggregates per statement and per head.

The runner is `coverage/`, a Lake project with `require veriphy from ".."`, `require physlib` at a pinned commit, and mathlib's `Archive` through `lake build Archive`. Its `Coverage.lean` imports `Physlib` and `Archive` and runs the command twice. Results are copied into `docs/development/coverage.md`.

### D8. Namespaces and library packs

Each entry record carries its namespace. The `mathlib` core is compiled into Veriphy. A library pack is a directory of JSON entries plus recipes. It names its library's root module (`Physlib`) and the constants it refers to. At extraction, Lean activates a pack when `(← getEnv).contains` holds for the pack's sentinel constant, so no import is needed. It then validates that each referenced constant exists, and reports a pack/library version mismatch, naming the missing constants. Resolution order is `mathlib`, packs in alphabetical order, then `project`. A conflict rejects the later entry.

**Alternative considered:** a separate Lake package per library (`veriphy-physlib`). That is heavier for users, and the pack is data, so it does not need compiling against Physlib.

### D9. `VeriphyCheck`: reflection with kernel evaluation

Each checker is a `Bool` function over the goal's own data, evaluated by `decide +kernel` (no `native_decide`), with a
soundness theorem into mathlib's statement. Matrix checkers take two forms:
- **Direct:** `mulCheck A B C` reads the goal's matrices. It is simple, but each entry of a `!![…]` literal costs a
  walk down its vector conses.
- **List-carrying:** the certificate states the rows of `A`, `B` and the product as lists, packed one natural number
  per row and decoded digit by digit, and builds matrices from them with the same vector conses a `!![…]` literal
  elaborates to. The goal's matrices then agree with the certificate's by unfolding, and the check walks lists.

Measured on this machine (Lean v4.34.1):
- **32×32 integer product, matrices given as definitions:** 4.4 s of kernel checking, 8 s in all.
- **The same identity stated with inline `!![…]` literals:** elaborating the statement alone costs about 60 s of
  typeclass inference, so large matrices belong in definitions.
- **Rational entries:** about 10× slower than integers, so the emitter clears denominators and checks over ℤ.
- **Polynomial identities, 462 monomials (`(a + b + c + d + e + 1)⁶`):** `ring` takes 140 s, and a kernel-evaluated
  sparse normalizer did not finish in 600 s. Polynomial identities therefore go to `ring` and `linear_combination`,
  and no polynomial checker ships.

The library is a separate `lean_lib` with mathlib as its only import, and `scripts/bundle_check.py` bundles it into
one file.

**Alternatives considered:**
- `native_decide`. It trusts the compiler, and the axiom guard rejects it.
- Entrywise `norm_num`. Proof size grows with every entry, and it is slower than kernel evaluation above about 8×8.

### D10. Exact number fields

Representations with square roots (Clebsch–Gordan coefficients), cyclotomic entries (fusion categories) and symbolic parameters (`D(2,1;α)`) need exact non-rational arithmetic. Sage computes in the number field or function field. Certificates come to Lean in one of three ways:
- **Over `ℚ(√d)`:** as pairs over ℚ, with an emitted `Real.sqrt d` rendering and `Real.sq_sqrt` facts.
- **Cyclotomic:** in `ℚ[x]/Φₙ`, with polynomial-reduction certificates checked by the polynomial checker, and the bridge to `CyclotomicField` through `IsPrimitiveRoot` facts.
- **Over `ℚ(α)`:** by clearing denominators into polynomial identities in `α`.

### D11. Component modules

Each component is a private toolkit module with a narrow public surface, re-exported from `veriphy.toolkit`:
- `_lie`: brackets, structure constants, Killing, Casimir, root data;
- `_representation`: representations, decompositions, Clebsch–Gordan;
- `_superalgebra`: grading, supertrace, super-Jacobi;
- `_operators`: test-function operators, normal ordering;
- `_clifford`: gamma matrices, traces, Fierz;
- `_geometry`: SageManifolds adapters for metrics, curvature, forms, contraction;
- `_algebraic`: Nullstellensatz, Positivstellensatz, normal forms, exponentials, Pratt;
- `_summation`: WZ, Gosper, Zeilberger, guessing;
- `_numerics`: series bounds, Sturm sequences, intervals;
- `_fusion`: fusion rings, F/R-symbols, gauge;
- `_reflect`: reflection emitters.

Each returns certificate objects with an `emit(problem)` method that produces Lean text, choosing the entrywise or reflective form by size. Technique search that is specific to one goal stays in recipe templates, as before.

### D12. Physics conventions are explicit parameters

Sign conventions (metric signature, `[Lᵢ, Lⱼ] = ±iεL`, Fierz basis normalization, gamma representation) are parameters of the component functions, never globals. The Physlib pack sets them to Physlib's conventions, and the templates expose them as `EDIT` lines.

### D14. `.veriphy/` as the project root of artifacts

A single Lean helper, `Veriphy.projectDir`, finds the workspace root (the nearest ancestor with a root lakefile, starting from the current directory). It returns `<root>/.veriphy`, and all readers and writers go through it: `sage_run file`, the translation loader, coverage output. Its Python mirror, `veriphy.core.project_dir(root=None)`, serves the catalogs. Directories are created on first write, never on read. Copied Lean assets go to `.veriphy/lean/`, which the project builds with:

```toml
[[lean_lib]]
name = "VeriphyAssets"
srcDir = ".veriphy/lean"
```

The recipes print this stanza.

**Alternatives considered:**
- Separate top-level directories (`certificates/`, `translations/`). That is the 0.1.0 state, and it scatters artifacts across the project root.
- A hidden directory outside the project (`~/.veriphy`). Artifacts must be committed with the proofs they serve.

### D13. One release, ordered work

Everything ships as 0.2.0. The task order still builds foundations first (layout, tables, coverage, checkers), because every component depends on them. A checkpoint after the foundations runs the full integration gate, so later components build on a green base.

### D14. `.veriphy/` as the project root of artifacts

A single Lean helper, `Veriphy.projectDir`, finds the workspace root (the nearest ancestor with a root lakefile, starting from the current directory). It returns `<root>/.veriphy`, and all readers and writers go through it: `sage_run file`, the translation loader, coverage output. Its Python mirror, `veriphy.core.project_dir(root=None)`, serves the catalogs. Directories are created on first write, never on read. Copied Lean assets go to `.veriphy/lean/`, which the project builds with:

```toml
[[lean_lib]]
name = "VeriphyAssets"
srcDir = ".veriphy/lean"
```

The recipes print this stanza.

**Alternatives considered:**
- Separate top-level directories (`certificates/`, `translations/`). That is the 0.1.0 state, and it scatters artifacts across the project root.
- A hidden directory outside the project (`~/.veriphy`). Artifacts must be committed with the proofs they serve.

### D13. Milestones

The tasks are ordered so that each milestone releases on its own:
- **0.2.0:** foundations (core coverage, namespaces and extensions, `VeriphyCheck`, coverage) and ODEs;
- **0.3.0:** Lie, representations, superalgebras, algebraic certificates;
- **0.4.0:** operators and Clifford, geometry, summation, numerics;
- **0.5.0:** fusion categories.

The change is archived once all milestones land. Each milestone runs the full integration gate and updates the coverage report.

## Risks / Trade-offs

- **[Risk]** A cast is lost when Sage rewrites a recorded sub-expression, and the rendered term then elaborates at an unintended type. → Integer-valued operators are typed by rule regardless, the outermost ascription fixes the expected type, and a wrong elaboration fails in Lean rather than proving something else.
- **[Risk]** Physlib's own mathlib pin drifts from Veriphy's. → The runner pins a Physlib commit whose manifest matches, and the report records both revisions. If none matches, the measurement runs on `Archive` alone and says so.
- **[Risk]** Project entries make problems larger, since they are serialized with every call. → Only entries whose Lean constant occurs in the problem are serialized.
- **[Trade-off]** Mirroring the core table in Lean and JSON duplicates one fact. → The agreement test makes the duplication checked rather than silent, and keeps the Lean side free of file I/O for the core.
- **[Risk]** Wider coverage makes Sage simplify more, so rendered results drift further from the goal's shape. → Recipes keep rendering from the script's own constructed expressions, and Lean checks every result regardless.

- **[Risk]** Kernel evaluation of large checkers is slow, even with GMP acceleration. → Sparse formats, and certificates sized to the claim (a basis rather than all products). Benchmarks in the test suite fix time budgets per checker. Above the budget, the template reports the size instead of emitting a proof that times out.
- **[Risk]** Sage's representation and fusion solvers return data in conventions (gauges, bases, normalizations) different from the goal's. → Conventions are explicit parameters (D12), gauge and basis changes are themselves certified, and templates report mismatches with the transformation that relates them.
- **[Risk]** SageManifolds and `ore_algebra` availability varies by Sage installation. → SageManifolds ships with Sage 10. `ore_algebra` is optional and named when missing, and the tests that need it are skipped with a reason when it is absent.
- **[Risk]** A library pack drifts from its library's API. → The pack validates its constants on activation and reports the missing ones. The pack's tests run in the coverage runner against the pinned Physlib.
- **[Trade-off]** Reference assets (coordinate geometry, fusion data) are definitions Veriphy did not get from mathlib. → They are mathlib-only, small, and written to be proposed upstream. Proofs against them are only as meaningful as the definitions, so each asset carries sanity theorems (the flat metric has zero curvature, the trivial fusion category satisfies the axioms).

## Migration Plan

The change is additive. Problems gain `extensions`, and conditions gain the `le` kind. Python accepts both shapes, and old daemons ignore the new fields. `symbolic` output may gain casts, and every existing test is rerun to confirm the text still closes its goals. Rollback is reverting the release. Committed proofs are unaffected, since they never contain `sage_run`.
