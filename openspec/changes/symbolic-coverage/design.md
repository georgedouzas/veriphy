# Design

## Context

The symbolic translation (`Veriphy/Kit/Symbolic.lean`) maps Lean terms to a small IR (`SymExpr`) through hard-coded tables, and records domain conditions as `(term, ne | nonneg | pos)`. `Problem.enrich` runs it over every hypothesis and the goal. The Python toolkit parses the serialized forms into Sage's symbolic ring (`parse_symbolic`) and renders results back with a function table in `_symbolic_emit.py`. Rendering is untyped: a term is printed and Lean elaborates it with whatever type unification finds. The `transcendental_rewrite` template keeps its own lemma table.

Physlib and Veriphy both pin mathlib `v4.34.1`, and mathlib declares an `Archive` library target, so one Lake project can import Veriphy, Physlib and `Archive` together.

## Goals / Non-Goals

**Goals:**
- One table format that serves the core entries and the project entries, in both directions.
- A semantic gap is either bridged by a domain condition or the term stays opaque, so Sage never simplifies a term whose Lean meaning differs.
- A coverage number that is reproducible from pinned revisions.

**Non-Goals:**
- Complex branch cuts beyond the existing `Complex` table (`Complex.log`, `Complex.arg` stay text-only).
- Integrals, limits and series. They are candidates for later, chosen by the coverage report.
- Running the coverage measurement in CI, since it needs a Physlib build.

## Decisions

### D1. Tables as data, one schema

Every function and rewrite entry, core or project, is a record with these fields:

```text
lean, arity, sage, applies_to (argument types), result type,
conditions [(argument index or pair, kind)], round_trip example
```

Rewrite entries carry `lemma`, `functions`, `reverse`, `side` and `example`. The core tables become a Lean array of such records, plus a mirrored JSON file shipped in the Python package (`veriphy/toolkit/core_table.json`). A Sage-free Lean test checks that the two agree. Project entries are JSON under `translations/`.

**Alternatives considered:**
- Code per entry, as now. It cannot be extended without a release.
- Lean attributes in the project, such as `@[veriphy_sage "cosh"]`. That would need the project to import a Veriphy elaborator into its own sources, and the daemon would still need the table. JSON is readable from both sides and reviewable as data.

### D2. Extensions travel with the problem

At extraction time, Lean loads `translations/*.json` from the workspace root and validates each file (field names, arity, condition kinds, Lean constant exists in the environment). It merges the project entries after the core entries, rejects conflicts, and serializes the merged project entries in the problem (`"extensions"`). Python renders from core plus `problem.extensions`, so both directions use one table per call. The loaded tables are cached per Lean process, keyed by the files' modification times.

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

`#veriphy_coverage [Prefix, …] "out.json"` iterates the environment's constants whose module starts with a prefix, keeping theorems only. For each, it runs `forallTelescopeReducing` on the type, collects relations from hypothesis types and the conclusion, and runs the symbolic pass (with the project's tables). It classifies atoms by `getAppFn`: an fvar head is uninterpreted, a const head is opaque. It aggregates per statement and per head.

The runner is `coverage/`, a Lake project with `require veriphy from ".."`, `require physlib` at a pinned commit, and mathlib's `Archive` through `lake build Archive`. Its `Coverage.lean` imports `Physlib` and `Archive` and runs the command twice. Results are copied into `docs/development/coverage.md`.

## Risks / Trade-offs

- **[Risk]** A cast is lost when Sage rewrites a recorded sub-expression, and the rendered term then elaborates at an unintended type. → Integer-valued operators are typed by rule regardless, the outermost ascription fixes the expected type, and a wrong elaboration fails in Lean rather than proving something else.
- **[Risk]** Physlib's own mathlib pin drifts from Veriphy's. → The runner pins a Physlib commit whose manifest matches, and the report records both revisions. If none matches, the measurement runs on `Archive` alone and says so.
- **[Risk]** Project entries make problems larger, since they are serialized with every call. → Only entries whose Lean constant occurs in the problem are serialized.
- **[Trade-off]** Mirroring the core table in Lean and JSON duplicates one fact. → The agreement test makes the duplication checked rather than silent, and keeps the Lean side free of file I/O for the core.
- **[Risk]** Wider coverage makes Sage simplify more, so rendered results drift further from the goal's shape. → Recipes keep rendering from the script's own constructed expressions, and Lean checks every result regardless.

## Migration Plan

The change is additive. Problems gain `extensions`, and conditions gain the `le` kind. Python accepts both shapes, and old daemons ignore the new fields. `symbolic` output may gain casts, and every existing test is rerun to confirm the text still closes its goals. Rollback is reverting the release. Committed proofs are unaffected, since they never contain `sage_run`.
