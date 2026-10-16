# Tasks

Every `lake build` and `lake env lean` runs under the build lock (D10), one Lean process at a time.

## 1. Replacement after acceptance (script-tactic)

- [x] 1.1 Report `Sage-free replacement` only after `closeAndEmit` succeeded and the axiom check passed (D9). Verify with a regression test in `VeriphyTest/SageRun.lean` whose block fails and whose messages contain no replacement.

## 2. Test fallback (test-fallback)

- [x] 2.1 Serialize a proposition's universal binders and body as a problem, reusing the existential-goal serialization (D2). Verify with Sage-free kit tests for a statement over `n : ℕ` and `A : Matrix (Fin n) (Fin n) ℚ`, and for a `def … : Prop`.
- [x] 2.2 Add the `sage_test` command (file and inline forms): instantiate the body at each instance, run its block, accept it under the axiom check and the independence check (D2). Verify with Lean tests: accepted instances, a circular instance rejected with the target named, a non-closing block rejected.
- [x] 2.3 Enforce three accepted instances with one edge case (D3), and emit the replacement: the examples and `veriphy_tested` with level and counts. Verify with tests for too few instances and for a replay with Sage absent.
- [x] 2.4 Write the test record `.veriphy/tests/<target>.json`, and add `python -m veriphy.certificates tests` with `--rerun` (D4). Verify with pytest on a recorded run: the listing, a rerun, and a rejected floating-point comparison.
- [x] 2.5 Add `#veriphy_levels` (D1). Verify with a Lean test on a module with a certified, a tested and a plain theorem.
- [x] 2.6 Add the `test_fallback` recipe document and template with the seeded sampler and edge cases (D3), and update `prompts/certify.md`, `prompts/prove.md` and the skills so that recipe selection runs first and the fallback names its level. Verify with `tests/recipes/test_templates.py` and the template's run in the Lean tests.

## 3. Translation (symbolic-translation)

- [x] 3.1 Vectors and vector operations in the matrix form (D6). Verify with kit tests for `*ᵥ`, `ᵥ*`, `⬝ᵥ`, `vecMulVec` and `diagonal`.
- [x] 3.2 Named matrices through their literal. Verify with a kit test on a project constant defined as a `4 × 4` literal.
- [x] 3.3 `Polynomial` with `X`, `derivative`, `eval` and `natDegree` (D6). Verify with kit tests and a round-trip test for `(X + 1) ^ 2`.

## 4. matrix_from_goal and tables (procedures)

- [x] 4.1 `4 × 4` determinants, transposes, symbolic entries and traces in the template (D7). Verify with one Lean test per shape.
- [x] 4.2 The `relations` option (D7). Verify with the boost and square-root eigenvector tests, and a rotation `R(θ)ᵀ R(θ) = 1`.
- [x] 4.3 Trigonometric entries in the core table, mirrored in `core_table.json`. Verify with the table-agreement test and `transcendental_rewrite` tests for power reduction, triple angle and the Pythagorean identity.
- [x] 4.4 The `definite_integral` recipe (D8). Verify with Lean tests for `cos²` over `[0, 2π]`, `sin 2φ` over `[0, 2π]` and a polynomial over `[0, 1]`.

## 5. Linear-algebra certificates (linear-algebra-certificates)

- [x] 5.1 `Veriphy/Kit/Linear.lean` packaging lemmas and the toolkit module `_linear.py` (D5). Verify with doctests, pytest, and an axiom audit of the lemmas.
- [x] 5.2 `independence` recipe. Verify with Lean tests for an independent family, a dependent one and a span equal to a kernel.
- [x] 5.3 `matrix_rank` recipe. Verify with Lean tests for rank one, full rank and a diagonal matrix.
- [x] 5.4 `dimension` recipe. Verify with Lean tests for a span, the kernel of the trace, an intersection and a tensor product.
- [x] 5.5 `nonlinearity` recipe. Verify with Lean tests for `x ^ 2` and a shifted bilinear form.
- [x] 5.6 `signature` recipe. Verify with Lean tests for a positive definite form and the Minkowski metric.

## 6. Release gate

- [x] 6.1 Run the goal shapes of the pilot report's missing-building-blocks list against the branch: each closes with a recipe or a `sage_test`. Verify by the Lean tests that state them (dimension, rank, independence and spans, vectors and named matrices, `matrix_from_goal` extensions and side relations, trigonometric rewrites, integrals, non-linearity, signatures, polynomials, the test fallback). Certifying the book's own pending claims is the book's task (its 11.6), not Veriphy's.
- [x] 6.2 Update the CHANGELOG, the recipe index, the user guide and the coverage page. Verify that the docs build.
- [x] 6.3 Run the full gate in order (formatting, checks, docs, tests, Lean tests). Verify that every session is green.
