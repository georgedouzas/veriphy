# Tasks

## 0. Project layout (project-layout, project-scripts)

- [x] 0.1 Add `Veriphy.projectDir` and `veriphy.core.project_dir` (D14), and route `sage_run file` through them, so bare names resolve in `.veriphy/certificates/`. Verify with tests: a bare name, an explicit `.veriphy/...` path, a run from a subdirectory, and a missing file naming the resolved path.
- [x] 0.2 Move the catalog to `.veriphy/certificates/` with `--root`, and add the 0.1.0 warning with its `git mv` command. Verify with pytest on a fixture with the old layout and one with the new.
- [x] 0.3 Update `prompts/prove.md`, `prompts/certify.md`, both skills, every recipe ("copy it to `.veriphy/certificates/`"), the README and the user guide to the `.veriphy/` layout, including the `lean_lib` stanza for copied assets. Verify that a grep finds no project-path `certificates/` outside `.veriphy/` in prompts, skills and docs, and that the docs build.

## 1. Baseline measurement (translation-coverage)

- [x] 1.1 Add `Veriphy/Kit/Coverage.lean` with `#veriphy_coverage [prefixes]` (writing to `.veriphy/coverage/` by default) (D7). It classifies atoms as local, uninterpreted or opaque, counts per statement and per head, and writes JSON plus a summary. Verify with Sage-free `#guard_msgs` tests in `VeriphyTest/Kit.lean` covering a fully covered statement, one with `Real.Gamma`, one with an uninterpreted `f x`, and one with no relation.
- [x] 1.2 Create the `coverage/` runner project: `require veriphy from ".."`, Physlib at a commit whose mathlib pin matches Veriphy's, and mathlib's `Archive`, `Mathlib.Analysis.ODE`, `Mathlib.Algebra.Lie` and `Mathlib.Geometry.Manifold`. Verify that `lake build` in `coverage/` produces one JSON report per corpus.
- [x] 1.3 Record the baseline in `docs/development/coverage.md`: corpus revisions, date, the three numbers per corpus and the top 30 opaque heads. Verify that the page builds with `nox -s docs -- build`.

## 2. Tables, conditions and namespaces (symbolic-translation, translation-extensions)

- [x] 2.1 Turn the core function table into data records with a namespace field (D1), and add the mirrored `core_table.json` in the Python package. Verify with a Sage-free Lean test that the two agree, and that the existing kit and round-trip tests stay green.
- [x] 2.2 Add the `le` condition kind with two terms and constant bounds (D3), including discharge by `b < a`. Verify with kit tests for `k ≤ n` discharged by `hk : k ≤ n` and by `hk : k < n`, and an undischarged one.
- [x] 2.3 Add `typed` sub-expressions and their serialization (D5). Verify with kit tests showing `typed(mod(x0, 7), 'ℕ')` for `((n % 7 : ℕ) : ℝ)`, and no marker in a pure ℕ goal.
- [x] 2.4 Add namespace resolution and library-pack activation by sentinel constant, with constant validation and conflict rejection (D8). Verify with kit tests using a fixture pack: inactive without its sentinel, active with it, a missing constant reported, and a conflict rejected.
- [x] 2.5 Create the `physlib` pack: `∂ₜ`, `∂[i]`, `lorentzAlgebra` membership, the ladder and angular-momentum operators' unfolding lemmas, and Physlib's sign conventions (D12). Verify in the coverage runner that the pack activates with Physlib, and that a Physlib statement using `∂ₜ` translates to a derivative.

## 3. Core coverage (symbolic-translation)

- [x] 3.1 Functions: `rpow`, `cosh`, `sinh`, `tanh`, `arctan`, `arcsin`, `arccos`, `Real.logb`, each with its conditions (D4). Verify with one kit test per function, showing its form and conditions.
- [x] 3.2 Sums and products over `Icc`, `Ico` and `range` with symbolic bounds, nested. Verify with kit tests, including a nested double sum.
- [x] 3.3 Integer functions, and integer `/`, `%` and ℕ subtraction with the gap rules (D4). Verify with kit tests: `n / 2` translated, `n / m` opaque without `0 < m`, `n - k` opaque without `k ≤ n` and translated with it.
- [x] 3.4 `deriv` of covered bodies at covered points, with conditions at the point. Verify with kit tests for `deriv (fun x => x ^ 2 * Real.exp x) 1` and `deriv (fun x => Real.log x) a`, the second listing `a ≠ 0`.
- [x] 3.5 Partial derivatives along a coordinate through `Function.update`. Verify with a kit test translating `deriv (fun t => f (Function.update x 0 t)) (x 0)` for an explicit `f`.

## 4. Rendering and emitters (symbolic-emitters)

- [x] 4.1 Bind `extensions` and `typed` in `read_problem`, and parse `typed` as the identity while recording marked sub-expressions. Verify with pytest on serialized problems containing each.
- [x] 4.2 Extend the rendering table and make rendering type-aware (D5), with a `type=` parameter and outermost ascription. Verify with pytest for each new function, for `((n % 7 : ℕ) : ℝ) + x`, and for rendering at ℕ, plus the Lean parse check.
- [ ] 4.3 Add the shared rewrite table across namespaces and `rewrite_candidates(problem)`, and move `transcendental_rewrite` onto it. Verify with pytest selecting `Real.log_mul` with its side conditions, and with the recipe's existing examples passing.
- [ ] 4.4 Add `has_deriv_at`, covering partial derivatives (D6). Verify with doctests, a pytest failure naming an undischarged `a ≠ 0`, and the Lean parse check.
- [ ] 4.5 Extend the round-trip suite with one example per new construct. Verify that `lake env lean VeriphyTest/SageRun.lean` passes with replay on.

## 5. Project tables (translation-extensions)

- [ ] 5.1 Load, validate and merge `.veriphy/translations/*.json` (D2): schema errors naming the file and field, conflicts naming both entries and namespaces, a per-process cache, and serialization of the entries the problem uses. Verify with kit tests on a fixture directory with valid, invalid and conflicting entries.
- [ ] 5.2 Add `veriphy.translations` (`list`, `show`, schema validation shared with the toolkit), showing namespaces. Verify with pytest on the fixture directory, and with a run of `sage -python -m veriphy.translations list`.
- [ ] 5.3 Add the round-trip check command for function and rewrite entries. Verify on the fixture directory: valid entries pass, and one with a wrong Sage name fails with its error.
- [ ] 5.4 Add the "unknown function" step to `prompts/certify.md` and the `certify` skill, the library-recipe section in the recipe index, and an example entry (`Real.arcosh`) in the user guide. Verify with a scratch project where `Real.arcosh` is opaque until the entry is added and checked, and is then translated.

## 6. Scalable checking (scalable-checking)

- [ ] 6.1 Create the `VeriphyCheck` library, mathlib-only, as its own `lean_lib` (D9). Verify that `lake build VeriphyCheck` succeeds, and that a grep finds no import outside mathlib.
- [ ] 6.2 Add the sparse rational matrix checker (product, sum, commutator, trace, equality) with `denote` and soundness theorems. Verify with tests proving a 64×64 commutation by `decide`, within a recorded time budget, and with the axiom guard accepting the proof.
- [ ] 6.3 Add the sparse polynomial checker with soundness. Verify on a polynomial identity of 2000 terms.
- [ ] 6.4 Add the structure-constant checker (bracket, Jacobi) with soundness into a Lie ring on `Fin n → ℚ`. Verify on 𝔰𝔩₃'s table, and on a corrupted table that fails.
- [ ] 6.5 Add the Pratt checker with soundness to `Nat.Prime`. Verify with `Nat.Prime 1000000007` and a 40-digit prime.
- [ ] 6.6 Add `_reflect` emitters with the size threshold and the bridge from `!![…]` literals (D9). Verify that a 2×2 identity emits the entrywise form, that a 16×16 identity emits the reflective form, and that both build without Sage.
- [ ] 6.7 Add `scripts/bundle_check.py`, producing one copyable `VeriphyCheck.lean`. Verify that the bundled file builds in a scratch project that has only mathlib.

## 7. Foundation recipes and ODEs (procedures, ode-bridge)

- [ ] 7.1 Write the `derivative` recipe and template. Verify that its worked example passes in `VeriphyTest/SageRun.lean` with replay on, and that the recipe-template pytest check passes.
- [ ] 7.2 Extend `sum_induction` to `Icc`/`Ico` sums. Verify with `∑ k ∈ Finset.Icc 1 n, (k : ℚ) = n * (n + 1) / 2` in the Lean suite.
- [ ] 7.3 Add ODE recognition in extraction (unknown function, variable, equation, initial conditions), including `∂ₜ` through the Physlib pack. Verify with kit tests on a second-order equation and on a Physlib-style `∂ₜ` statement.
- [ ] 7.4 Add the ODE substitution emitter and the `ode_solution` recipe. Verify on the harmonic oscillator with initial conditions, on `x' = 2x` with `x 0 = 3` as an existential, and on a solution that fails with Lean's residual goal shown.
- [ ] 7.5 Verify that `transcendental_rewrite` selects a project rewrite entry (`Real.cosh_sq` from a fixture) without edits, in a scratch project.

## 8. Foundations checkpoint

- [ ] 8.1 Rerun the coverage runner and record the post-change numbers and classified top heads. Verify that the fully covered share is at least the baseline's for every corpus.
- [ ] 8.2 Update the user guide (namespaces, project tables, typed rendering, ODEs, `VeriphyCheck`), the developer guide (adding core entries, packs and checkers), the README and the recipe index. Verify that `nox -s docs -- build` succeeds.
- [ ] 8.3 Run `nox -s checks`, `nox -s tests`, `lake build VeriphyTest`, `lake build VeriphyCheck` and the Sage-free replay of every replacement, all green. Push and verify that CI is green.

## 9. Lie algebras (lie-bridge)

- [ ] 9.1 Translate `⁅A, B⁆` on matrices and on matrix Lie subalgebra elements, and matrices indexed by `Fin n` and by sums of `Fin` types, with index order recorded. Verify with kit tests on a 2×2 bracket and a `Fin 1 ⊕ Fin 3` matrix.
- [ ] 9.2 Add `_lie`: structure constants from a basis, closure check, Killing form, Casimir, with entrywise or reflective emission. Verify on 𝔰𝔩₂ (bracket table, Casimir commuting) and on 𝔰𝔲(3) through the structure-constant checker.
- [ ] 9.3 Add root data (Cartan matrices, inverses, Weyl group orders, positive roots) as checked statements against mathlib's `CartanMatrix`. Verify with `CartanMatrix.E₈.det = 1` and the inverse of `CartanMatrix.F₄`.
- [ ] 9.4 Write `lie_structure` and the Physlib Lorentz-algebra recipe. Verify their worked examples in the Lean suite (the Physlib one in the coverage runner).

## 10. Representations (representation-bridge)

- [ ] 10.1 Add exact number-field support (D10): `ℚ(√d)`, cyclotomic quotients and `ℚ(α)`, with rendering and bridge facts. Verify with pytest and Lean examples for one identity in each field.
- [ ] 10.2 Add `_representation`: explicit representations from a Cartan type and highest weight, or from matrices, with bracket-relation proofs. Verify on the adjoint of 𝔰𝔩₃.
- [ ] 10.3 Certify decompositions by intertwiners and projectors, including branching through embedding matrices. Verify on two spin-½ representations, and on 10 of SU(5) to SU(3)×SU(2)×U(1).
- [ ] 10.4 Add Clebsch–Gordan coefficients with intertwining proofs. Verify on 1 ⊗ ½.
- [ ] 10.5 Write the `representation` recipe. Verify its worked examples in the Lean suite.

## 11. Lie superalgebras (representation-bridge)

- [ ] 11.1 Add `_superalgebra`: grading, graded bracket, supertrace, super-Jacobi, invariant form and Casimir for explicit supermatrices. Verify on `sl(1|1)` and `osp(1|2)`.
- [ ] 11.2 Build the exceptional families `D(2,1;α)` (symbolic α), `G(3)` and `F(4)` in defining representations. Verify super-Jacobi for `D(2,1;α)` over `ℚ(α)`, and for `F(4)` through the reflective checker.
- [ ] 11.3 Write the `lie_superalgebra` recipe. Verify its worked example in the Lean suite.

## 12. Algebraic certificates (algebraic-certificates)

- [ ] 12.1 Add Positivstellensatz search (SOS multipliers) and Nullstellensatz and radical certificates (Gröbner). Verify on the spec's scenarios.
- [ ] 12.2 Add Smith and Jordan normal forms and diagonalizations with inverse certificates. Verify on an integer matrix and on a matrix with a nontrivial Jordan block.
- [ ] 12.3 Add matrix exponentials against mathlib's `exp` (nilpotent, diagonalizable, ODE characterization). Verify on a Lorentz boost and on a nilpotent 3×3 matrix.
- [ ] 12.4 Add Pratt certificate search wired to the checker. Verify on a 40-digit prime.
- [ ] 12.5 Write `infeasibility`, `matrix_normal_form`, `matrix_exponential` and `primality`. Verify their worked examples in the Lean suite.

## 14. Operators and Clifford algebras (operator-bridge)

- [ ] 14.1 Add `_operators`: operators from multiplications and partial derivatives applied to a symbolic test function, with commutators and test-function proofs. Verify on `[d/dx, x]` and on `[L₁, L₂]` under `ContDiff ℝ 2 ψ`.
- [ ] 14.2 Add matrix-operator normal ordering and commutators. Verify on the Pauli matrices and on truncated ladder operators.
- [ ] 14.3 Add `_clifford`: gamma matrices by representation and signature, the Clifford relation, traces with `γ⁵`, contraction identities and Fierz coefficients. Verify the four-gamma trace for all index combinations through the reflective checker, and the Fierz matrix.
- [ ] 14.4 Write `operator_identity` and the Physlib ladder-operator recipe. Verify their worked examples, the Physlib one in the coverage runner.

## 15. Coordinate geometry (coordinate-geometry-bridge)

- [ ] 15.1 Write the mathlib-only asset `CoordinateGeometry.lean`: Christoffel symbols, Riemann, Ricci, scalar curvature, Killing equation, forms (d, wedge, Hodge star) and contraction, with sanity theorems (flat metric, `d ∘ d = 0` on polynomial forms). Verify that it builds in a mathlib-only scratch project.
- [ ] 15.2 Add `_geometry` adapters to SageManifolds, with componentwise emission. Verify on the 2-sphere (`Γ^θ_φφ`), Minkowski (all zero), and the Killing vector `∂_φ`.
- [ ] 15.3 Add forms and contraction emission. Verify on an exact 1-form on ℝ³ with its primitive, and on `F_{μν} F^{μν}`.
- [ ] 15.4 Write `coordinate_geometry`. Verify its worked examples in the Lean suite.

## 16. Summation (summation-certificates)

- [ ] 16.1 Add `_summation`: WZ pairs, Gosper and Zeilberger, with telescoping and induction proofs and denominator conditions. Verify on the binomial sum and the Gosper example.
- [ ] 16.2 Add recurrence guessing and verification, with `ore_algebra` optional and named when missing. Verify on `a (n + 2) = 5 a (n + 1) - 6 a n`, and on the missing-package message.
- [ ] 16.3 Write `wz_certificate` and `recurrence`, and point `sum_induction` at them. Verify their worked examples.

## 17. Certified numerics (certified-numerics)

- [ ] 17.1 Add `_numerics`: series truncations with rational remainder bounds for `exp`, `log`, `sin`, `cos`, `arctan` and π, chosen by interval arithmetic, with mathlib's bounds preferred. Verify on `Real.exp 1 < 2.7183` and `3.14159 < Real.pi`.
- [ ] 17.2 Add root isolation by Sturm sequences with sign certificates and the intermediate value theorem, and eigenvalue bounds through characteristic polynomials. Verify on the spec's cubic and on a 3×3 symmetric matrix.
- [ ] 17.3 Write `certified_bound` and `root_isolation`. Verify their worked examples and the `Gamma` refusal.

## 19. Fusion categories (fusion-category-bridge)

- [ ] 19.1 Write the mathlib-only asset `FusionData.lean` (multiplicity-free fusion data, pentagon and hexagon equations), with the trivial category as a sanity theorem. Verify that it builds in a mathlib-only scratch project.
- [ ] 19.2 Add `_fusion`: fusion rings and F/R-symbols from Sage, the associativity, pentagon and hexagon proofs over cyclotomic fields, and gauge transformations. Verify on SU(2) level 2, Fibonacci (pentagons) and Ising (hexagons over `ℚ(ζ₁₆)`).
- [ ] 19.3 Add naturality certificates for explicit linear natural transformations. Verify on an intertwiner between two representations of a finite group.
- [ ] 19.4 Write `fusion_category`. Verify its worked examples and the gauge-mismatch report.

## 20. Release gate

- [ ] 20.1 Rerun the coverage runner and record the final numbers and classified heads; update the docs with a chapter per component family (algebra, analysis and physics, categories) and the full recipe index. Run `nox -s checks`, `nox -s tests`, `lake build VeriphyTest`, `lake build VeriphyCheck` and the Sage-free replay, all green. Push and verify that CI is green.
- [ ] 20.2 Run `openspec validate symbolic-coverage --strict` and verify that it passes.

## Workflow follow-up

- Archive the change, merge to `main`, and release 0.2.0 through the release flow. PyPI trusted publishing must be configured first.
