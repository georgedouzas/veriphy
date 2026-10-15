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

The exact list follows the book's pilot chapter, which measures which goals no recipe closes; the gaps known before
the pilot are:

- **Rotation exponentials:** `NormedSpace.exp` of generators with eigenvalues `±i` (rotations, `SU(2)` elements),
  excluded today by `matrix_exponential`.
- **Grassmann variables:** identities in exterior algebras over a jet ring (supersymmetry transformations, Berezin
  integrals).
- **Definite and improper integrals:** over intervals and the real line, with Gaussian moments, Gamma and Beta values
  and Fourier coefficients as the target shapes, reusing mathlib's interval-integral and Gaussian-integral lemmas.
- **Contour integrals and residues** of rational and meromorphic functions.
- **Limits** of sequences and functions, with explicit `ε`-`N` and `ε`-`δ` witnesses.
- **Series closed forms** beyond `sum_induction`: zeta values at even integers, geometric and Matsubara-type sums.
- **Special-function identities:** Legendre, Hermite and Bessel recurrences and orthogonality, spherical harmonics as
  Laplacian eigenfunctions.
- **Integrals of differential forms** over explicit manifolds: Stokes on a disc, Chern numbers of explicit connections.
- **Probability:** expectations and moments of discrete and continuous distributions.
- **Finite groups at scale:** coset decompositions, character tables and orbit counts beyond what `decide` handles.
- **Documentation:** the `VeriphyAssets` module-name clash for downstream projects that copy the assets.

Each addition comes with its recipe document and template under `prompts/recipes/`, tests, translation-table entries
where needed, and a CHANGELOG entry, for the next minor release.

## Capabilities

### New Capabilities

To be determined by the design, after the pilot.

### Modified Capabilities

- `certificates`: new recipes and emitters.

## Impact

Python package (`src/veriphy/`), Lean libraries (`Veriphy`, `VeriphyCheck`, `VeriphyAssets`), recipe documents and
templates, tests. No breaking change is planned.
