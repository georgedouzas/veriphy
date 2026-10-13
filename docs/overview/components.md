# Components

Veriphy's toolkit is organized by family. Each component follows the same contract: Sage computes, untrusted, and
checks its own answer first, naming what fails; the result reaches Lean as a certificate that the kernel or a
standard tactic checks; the replacement Veriphy prints builds without Sage. Large finite checks go through the
`VeriphyCheck` library (kernel evaluation with a soundness theorem); definitions mathlib lacks are recipe assets,
mathlib-only Lean files a project copies to `.veriphy/lean/VeriphyAssets/`.

The [user guide](user_guide.md#building-proofs-with-sage_run) indexes the recipes by goal shape; the
[API reference](../api/) documents every toolkit function.

## Algebra

| Component | Sage computes | Lean checks | Recipes |
|---|---|---|---|
| Lie algebras (`_lie`) | structure constants, Killing and trace forms, Casimirs, Cartan matrices, Weyl group orders, positive roots | bracket relations and Jacobi by `VeriphyCheck` (`bracket_eq_of_check`, `jacobi_of_check`); determinants by an LU factorization (`det_eq_of_lu`); inverses by a product | `lie_structure`, `physlib/lorentz_algebra` |
| Representations (`_representation`) | defining, spin, adjoint, tensor and exterior representations, cyclic submodules, projectors, intertwiners, decompositions, Clebsch–Gordan matrices | every claim as a matrix identity (`mul_eq_mul_of_check`, `commute_of_check`) | `representation` |
| Lie superalgebras (`_superalgebra`) | graded brackets, supertraces, invariant forms, super-Casimirs; `sl(m\|n)`, `osp`, `D(2,1;α)`, `G(3)`, `F(4)` by moment maps; integral rescalings | super-Jacobi by the sparse checker (`VeriphyCheck.Sparse`), with the cyclic reduction; families in `α` by affinity | `lie_superalgebra` |
| Number fields (`_number_field`) | reductions in `ℚ(√d)`, cyclotomic fields and function fields `ℚ(α)` | identities by `linear_combination` with the minimal relation; matrices over `ℚ(√5)`, `ℤ[i]` and `ℚ(ζ₁₆)` by kernel evaluation | used by the others |
| Algebraic certificates (`_algebraic`) | Nullstellensatz and radical lifts (Gröbner), Positivstellensatz weights (exact LP) | `linear_combination`, `pow_eq_zero_iff` | `infeasibility` |
| Primality (`_reflect`) | Pratt certificates | the kernel (`VeriphyCheck.Pratt`) | `primality` |
| Normal forms and exponentials (`_normal_form`, `_exponential`) | Smith and Jordan forms with transformations; nilpotent and diagonalizable exponentials | the transformations as matrix identities; `NormedSpace.exp` through the series or the diagonalization | `matrix_normal_form`, `matrix_exponential` |

## Analysis and physics

| Component | Sage computes | Lean checks | Recipes |
|---|---|---|---|
| ODEs (`_ode`, `_derivative`) | solutions of linear and separable equations | derivatives by structural `HasDerivAt`, then the equation by `ring` or `field_simp` | `ode_solution`, `derivative` |
| Operators and Clifford algebras (`_operators`, `_clifford`) | commutators of differential operators on a test function; Pauli, spin and ladder matrices; gamma matrices, traces, Fierz coefficients; commutators of Physlib's ladder operators from `[x, p] = iℏ` | operator identities pointwise (`simp` with derivative lemmas, `fun_prop`, symmetry of second derivatives); matrix identities entrywise; Physlib's commutation lemmas | `operator_identity`, `physlib/ladder_operators` |
| Coordinate geometry (`_geometry`) | Christoffel symbols and curvature with SageManifolds; primitives of closed forms; field-strength contractions | the components from the `CoordinateGeometry` asset's definitions | `coordinate_geometry` |
| Summation (`_summation`) | WZ mates and Gosper antidifferences (sympy), closed forms of recurrences, guessed recurrences (`ore_algebra`) | the summand identity, telescoping by `Finset.sum_range_sub`, induction | `wz_certificate`, `recurrence` |
| Certified numerics (`_numerics`) | interval enclosures of `exp`, `log`, `sin`, `cos`, `π`; isolating intervals of real roots; characteristic polynomials | mathlib's series remainder bounds and decimal bounds; roots by the intermediate value theorem and monotonicity | `certified_bound`, `root_isolation` |

## Categories

Abstract category theory stays with mathlib's automation (`aesop_cat`, `simp`, coherence). Veriphy covers explicit
finite data.

| Component | Sage computes | Lean checks | Recipes |
|---|---|---|---|
| Fusion categories (`_fusion`) | fusion rules from `FusionRing` (refusing multiplicities above 1); Fibonacci F-symbols in `ℚ(√5)` by a Gröbner solve; Ising F- and R-symbols in `ℚ(ζ₁₆)`; pentagon and hexagon violations; gauges relating two data | the `FusionData` asset: the kernel checks the pentagons and hexagons on admissible labels, with values as coefficient lists on the power basis of `ζ`, and the asset's theorems give them at every `ζ` with the same minimal relation in every `ℚ`-algebra (over `ℂ` at `exp (2πi/16)`, and at the Galois conjugates); gauge relations likewise | `fusion_category` |
| Natural transformations (`_representation`) | intertwiners between representations of a finite group | the naturality square per generator by the kernel; `VeriphyCheck.intertwines_of_closure` extends it to the group; `repHom` and `repIso` package it as a morphism or isomorphism of `Rep` | `fusion_category` |

## Checkers and assets

| `VeriphyCheck` module | Checks |
|---|---|
| `Matrix` | matrix products and identities over computable rings |
| `StructureConstants` | brackets and the Jacobi identity from structure constants |
| `SuperStructureConstants` | the super-Jacobi identity, dense and sparse |
| `Determinant` | determinants by LU factorizations, inverses by products |
| `Pratt` | primality by Pratt certificates |
| `Intertwiner` | intertwiners from generators; morphisms and isomorphisms of `Rep` |

| Asset | States |
|---|---|
| `CoordinateGeometry` | Christoffel symbols, Riemann and Ricci tensors, scalar curvature, Killing equation, forms with exterior derivative, wedge and Hodge star |
| `FusionData` | multiplicity-free fusion data, pentagon and hexagon equations, gauge transformations, coefficient-list data |
