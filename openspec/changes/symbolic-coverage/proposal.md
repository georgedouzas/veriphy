# Proposal

## Why

Symbolic translation (0.1.0) covers field arithmetic, the elementary `Real`/`Complex` functions, range sums, matrices and polynomials. Anything else becomes an opaque atom, and a script cannot reason about it. No translator can be exhaustive, since mathlib grows every week. So the next release does three bounded things:
- it finishes a core that real goals actually use;
- it lets projects extend the tables themselves, with no Veriphy release;
- it measures coverage on real statements, so new entries follow data rather than guesses.

## What Changes

- **Core coverage, five categories.** Each new construct comes with its domain conditions, and with explicit handling where Lean and Sage disagree on meaning:
  - **Functions:** `rpow` with real exponents, `cosh`, `sinh`, `tanh`, `arctan`, `arcsin`, `arccos` and `Real.logb`. A shared rewrite table gains `exp_log`, `log_exp`, `log_mul`, `log_div`, `log_rpow`, `sqrt_mul_self`, `cosh_sq` and similar entries, each with its side conditions.
  - **Sums and products** over `Finset.Icc`, `Finset.Ico` and `Finset.range` with symbolic bounds, including nested sums.
  - **Integer functions:** `Nat.factorial`, `Nat.choose`, `Nat.gcd`/`Int.gcd`, `Int.floor`, `Int.ceil`, and integer division and remainder.
  - **Typed rendering.** Rendered terms carry the casts and type ascriptions Lean needs, so `n % 7` on ℕ never elaborates as a real remainder. ℕ subtraction translates only when `b ≤ a` is known, because Lean truncates it.
  - **Calculus:** `deriv` of explicit expressions translates to Sage's derivative at the point. A new emitter builds the matching `HasDerivAt` proof term, and a new `derivative` recipe uses it.
- **Domain conditions generalize** from `≠ 0`, `0 ≤`, `0 <` on one term to also cover `a ≤ b` between two terms. They are needed for ℕ subtraction and inverse-trigonometric domains.
- **Project translation tables.** A project's `translations/` directory holds extra entries as JSON files: a Lean constant, its Sage name, arity, argument types, domain conditions, optional rewrite lemmas, and a round-trip example.
  - Both directions read the entries: Lean translation and toolkit rendering.
  - They are listed by `sage -python -m veriphy.translations list`.
  - A Lean command checks every entry's round trip.
  - An agent that meets an unknown function (for example `Real.cosh` before this change) adds an entry and its test, with no Veriphy release.
  - The `certify` playbook gains the step for doing so.
- **Coverage measurement.** A Sage-free Lean command walks the theorem statements of chosen modules and runs the symbolic translation on their relations. It reports:
  - the share of statements translated with no opaque atom;
  - the share with only uninterpreted local functions left;
  - a ranked list of the most frequent opaque head constants.

  A runner project measures Physlib and Mathlib's `Archive`. The baseline and the post-change numbers are recorded in `docs/development/coverage.md`.

## Capabilities

### New Capabilities
- `certificates/translation-extensions`: project-local translation and rewrite entries, their file format, discovery, round-trip checking, conflict rules, and the agent workflow for adding one.
- `certificates/translation-coverage`: measuring how much of a corpus of statements the translation covers, and reporting the opaque heads that matter most.

### Modified Capabilities
- `certificates/symbolic-translation`: the coverage list grows by the five categories, domain conditions gain the two-term `≤` kind, and semantic gaps (ℕ subtraction, integer division, inverse-trigonometric clamping, `rpow` of negative bases, `deriv` at non-differentiable points) must be handled by conditions or by leaving the term opaque.
- `certificates/symbolic-emitters`: the function table grows, rendering becomes type-aware, rewrite entries come from one shared table (core and project), and derivative proofs get an emitter.
- `certificates/procedures`: the recipe set gains `derivative`, and `sum_induction` covers `Icc`/`Ico` sums.

## Impact

- **Lean:**
  - `Veriphy/Kit/Symbolic.lean` gains the new tables, the extension loader, the two-term condition kind and typed sub-expressions;
  - new `Veriphy/Kit/Coverage.lean` (the measurement command) and a round-trip checking command for extensions;
  - `Veriphy/Kit/Problem.lean` serializes the project's entries with the problem.
- **Python:**
  - `veriphy.toolkit` gains type-aware rendering, the shared rewrite table and the `HasDerivAt` emitter;
  - a new `veriphy.translations` catalog (`list`, `show`, schema validation).
- **Recipes and playbooks:**
  - a new `prompts/recipes/derivative.md`, and `sum_induction` updated;
  - `transcendental_rewrite` reads the shared rewrite table;
  - `prompts/certify.md` gains the "unknown function" step.
- **Corpus runner:** a separate Lake project under `coverage/`, requiring Veriphy by path and Physlib at a pinned revision. Mathlib's `Archive` comes through mathlib. It is not part of the library build or CI.
- **Docs:** user guide (extensions), developer guide (adding a core entry), `docs/development/coverage.md`.
- **Compatibility:** additive. Existing scripts keep working. The rendered text of `symbolic` may now include casts and ascriptions it previously omitted.
- **Release:** targets 0.2.0.
