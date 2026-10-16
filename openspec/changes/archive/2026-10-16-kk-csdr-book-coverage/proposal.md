# Proposal

## Why

The book *Kaluza-Klein Theories and Coset Space Dimensional Reduction* verifies every claim it makes with Veriphy:
every definition, theorem, example and exercise answer, about 5,600 blocks, across set theory, linear algebra, real and
complex analysis, differential equations, Fourier analysis, operator theory, probability, differential geometry, Lie
theory, classical mechanics, statistical mechanics, quantum mechanics, field theory, gravity, supersymmetry and
dimensional reduction. Its rule is that a missing building block is added to Veriphy rather than replaced by a
hand-written proof in the book. Veriphy 0.2.0 already covers polynomial identities, matrices, Lie structure,
representations, derivatives, ODE solutions and coordinate geometry. The book's computations show where the coverage
ends.

## What Changes

The book's pilot chapter (linear algebra, 527 claims, 404 Lean declarations) measured the coverage: 39 % of its
theorems were closed by a recipe, and 61 % needed a hand-written mathlib proof. The change closes the measured gaps and
adds a fallback for claims that admit no certificate.

- **Test fallback (new).** When no recipe can build a certificate, Veriphy still checks the claim, by testing it. A
  `sage_test` command takes a formal statement `∀ x, P x`, lets a Sage script choose instances, and has the Lean kernel
  check each instance by computation alone, with a proof that does not use the theorem under test. Instances that Lean
  cannot state are evaluated by Sage alone and kept in a test record. Every result carries its level (certificate,
  kernel-checked test, oracle test), so a test is never shown as a proof.
- **Linear-algebra certificates (new):** `dimension` (finrank of spans, kernels, intersections, matrix and tensor
  spaces), `matrix_rank`, `independence` (linear independence, dependence and span equalities of explicit vectors),
  `nonlinearity` (refuting that a given map is linear or bilinear) and `signature` (an explicit congruence to a
  diagonal form).
- **Translation:** vectors and vector operations (`![…]`, `*ᵥ`, `ᵥ*`, `⬝ᵥ`, `vecMulVec`, `diagonal`), named matrix
  definitions, and `Polynomial` (with `X` as a generator, `derivative`, `eval`, `natDegree`).
- **`matrix_from_goal`:** `4 × 4` determinants, products with transposes, symbolic entries, traces, and identities
  modulo side relations (`cosh² − sinh² = 1`, `(√a)² = a`, `cos² + sin² = 1`), which also covers rotation and boost
  matrices.
- **`transcendental_rewrite` tables:** Pythagorean, power-reduction and multiple-angle entries.
- **Definite integrals:** a `definite_integral` recipe for interval integrals with an elementary antiderivative.
- **`sage_run` messages:** the `Sage-free replacement` is reported only after the kernel accepted the block.

The gaps the proposal listed before the pilot and that linear algebra does not exercise (Grassmann variables, contour
integrals, limits, series closed forms, special functions, integrals of forms, probability, finite groups at scale)
stay in scope of this change. They are specified and implemented when the book's chapters that need them are
certified, each measured the way the pilot measured linear algebra.

## Capabilities

### New Capabilities

- `certificates/test-fallback`: the `sage_test` command, its levels, its test record and its recipe.
- `certificates/linear-algebra-certificates`: the dimension, rank, independence, non-linearity and signature recipes.

### Modified Capabilities

- `certificates/script-tactic`: the replacement message only after acceptance.
- `certificates/symbolic-translation`: vectors, named matrices and polynomials.
- `certificates/procedures`: `matrix_from_goal` extensions, the side-relation option, the trigonometric table entries
  and the `definite_integral` recipe.

## Impact

Python package (`src/veriphy/`), Lean libraries (`Veriphy`, `VeriphyCheck`), recipe documents and templates under
`prompts/recipes/`, the agent prompts and skills that choose a recipe, tests in `tests/` and `VeriphyTest/`, the
CHANGELOG. No breaking change: existing recipes keep their behaviour, and the fallback is a new command.
