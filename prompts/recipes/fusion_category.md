# Fusion categories

## When to use

- The goal states that **explicit multiplicity-free fusion data** (anyon models: Fibonacci, Ising, `SU(2)_k`) form a
  fusion or braided fusion category, with the `FusionData` asset: `FusionData.IsFusion (RepData.toData E ζ)` (fusion
  ring axioms and every pentagon equation) or `FusionData.IsBraidedFusion` (also both hexagons), or that two data
  differ by a gauge transformation (`FusionData.GaugeRelated`).
- Copy the asset `assets/VeriphyAssets/FusionData.lean` to the project's `.veriphy/lean/VeriphyAssets/FusionData.lean`
  and declare the `VeriphyAssets` library (see the user guide). It imports mathlib only.
- Values live in a number field `ℚ(ζ)` with `ζ ^ m = r`: `ℚ(√5)` (`ζ² = 5`) for Fibonacci, `ℚ(ζ₁₆)` (`ζ⁸ = -1`) for
  Ising. A `RepData` stores them as rational coefficients on `1, ζ, ζ², …`; `RepData.toData E ζ` evaluates them at
  any `ζ` in any `ℚ`-algebra (`√5` in `ℝ`, `exp (2πi/16)` in `ℂ`, or a variable with a hypothesis).
- Sage builds the data (`fibonacci()`, `ising()`, `fusion_rules(type, level)` from `FusionRing`) and checks
  associativity, pentagons and hexagons, naming what fails. The kernel then checks the goal's data once, on the
  coefficient lists and on admissible labels only; the asset's theorems give the full equations at every `ζ` with the
  same relation. Ising's braided check takes a few seconds.
- For **natural transformations** between explicit representations (functors from a group's one-object category),
  use `naturality_proof` from the representation toolkit: Sage checks the square for each generator, the kernel
  checks it again, and `VeriphyCheck.intertwines_of_closure` extends it to the group; `VeriphyCheck.repHom` and
  `repIso` (with `natural_iso_facts`) make it a morphism or isomorphism of `Rep`.

## Template

Copy it to the project's `.veriphy/certificates/fusion_category.sage` (or a more specific name), adapt the lines
marked `EDIT`, keep the header, and run it with `sage_run file "<name>.sage"`.

```sage
# name: fusion_category
# technique: fusion rules, pentagon and hexagon equations over number fields, gauge transformations
# goal: FusionData.IsFusion or IsBraidedFusion of explicit data (RepData.toData E ζ), or FusionData.GaugeRelated
# description: Sage builds and checks the data and finds gauges; the kernel checks the equations on coefficient lists.
REFERENCE = None  # EDIT: fibonacci(), ising(), or a Fusion with F- and R-symbols (fusion_rules('A1', k) gives rules)
TARGET = None  # EDIT: the goal's data as a Fusion when its gauge may differ from REFERENCE's; None when they agree
KIND = 'fusion'  # EDIT: 'fusion' (IsFusion or IsBraidedFusion) or 'gauge' (GaugeRelated REFERENCE TARGET)
BRAIDED = True  # EDIT: False for IsFusion (the pentagons only)
ROOT = True  # EDIT: False when ζ is a variable with `hζ : ζ ^ m = algebraMap ℚ K r` in the context
assert REFERENCE is not None, 'fill in REFERENCE in a copy'
data = REFERENCE if TARGET is None else TARGET
if TARGET is not None:
    print(gauge_mismatch(REFERENCE, TARGET))  # the differing symbols, and the gauge relating them if there is one
if KIND == 'gauge':
    u = find_gauge(REFERENCE, TARGET)
    assert u is not None, 'no gauge in the field relates the data: ' + gauge_mismatch(REFERENCE, TARGET)
    print('gauge:', gauge_term(u, REFERENCE))
    print('inverse:', gauge_term(u, REFERENCE, inverse=True))
    proof = gauge_proof(REFERENCE, TARGET, u, root=ROOT)
else:
    print(fusion_data_term(data))  # the data as a Lean RepData, to define in the project
    proof = fusion_proof(data, braided=BRAIDED, root=ROOT)
```

## Worked examples

```lean
-- `ising` is the RepData that `fusion_data_term(ising())` prints (REFERENCE = ising())
example : FusionData.IsBraidedFusion
    (FusionData.RepData.toData ising (Complex.exp (2 * Real.pi * Complex.I / 16))) := by
  sage_run file "ising_braided.sage"

-- at every root of x⁸ + 1, with ROOT = False
example {K : Type} [CommRing K] [Algebra ℚ K] (ζ : K) (hζ : ζ ^ 8 = algebraMap ℚ K (-1)) :
    FusionData.IsBraidedFusion (FusionData.RepData.toData ising ζ) := by
  sage_run "proof = fusion_proof(ising(), braided=True, root=False)"

-- the goal's Fibonacci F-symbols are in another gauge (KIND = 'gauge'): the template prints the mismatch and the
-- gauge, which the goal names as `gauge` and `gaugeInv`
example : FusionData.GaugeRelated (FusionData.RepData.toData fib (Real.sqrt 5))
    (FusionData.RepData.toData fib₂ (Real.sqrt 5))
    (fun a b c => FusionData.Coeffs.eval (Real.sqrt 5) (gauge a b c))
    (fun a b c => FusionData.Coeffs.eval (Real.sqrt 5) (gaugeInv a b c)) := by
  sage_run file "fibonacci_gauge.sage"

-- summing coordinates is natural from the permutation representation of S₃ to the trivial one
example : ∀ g, (!![1, 1, 1] : Matrix (Fin 1) (Fin 3) ℚ) * perm g = triv g * (!![1, 1, 1] : Matrix (Fin 1) (Fin 3) ℚ) := by
  sage_run "
cycle = matrix(QQ, [[0, 0, 1], [1, 0, 0], [0, 1, 0]])
swap = matrix(QQ, [[0, 1, 0], [1, 0, 0], [0, 0, 1]])
one = identity_matrix(QQ, 1)
proof = naturality_proof(matrix(QQ, [[1, 1, 1]]), [cycle, swap], [one, one], rho='perm', sigma='triv',
    closure='generators')"
```

`VeriphyTest/SageRun.lean` also proves the Fibonacci pentagons over `ℝ`, states the `SU(2)` level 2 fusion rules as
facts, and builds the S₃ intertwiner as a morphism of `Rep`.

## Failure modes

- **"fill in REFERENCE in a copy":** copy the template and choose the data.
- **"has a fusion multiplicity above 1":** the category (`SU(3)` at level 3, for instance) is not multiplicity free;
  its F-symbols are matrices on multiplicity spaces, outside the asset.
- **"N pentagon equations fail" or "N hexagon equations fail":** the F- or R-symbols are wrong, or belong to a
  different category with the same rules (`SU(2)` at level 2 and Ising differ in the sign of `F^{σσσ}_σ`).
- **The goal's symbols differ from Sage's (`decide` fails on the goal's data):** set `TARGET` to the goal's data; the
  template prints the differing symbols and the gauge relating them (`KIND = 'gauge'` certifies it). "no gauge in the
  field relates the data" means a different category, or a gauge needing a field extension.
- **"the naturality square fails at generator k":** the matrix is not an intertwiner; `intertwiners(rho, sigma)`
  computes a basis of those that are.
- **Abstract categorical statements** (monoidal coherence, limits, adjunctions) stay with mathlib's automation
  (`aesop_cat`, `simp`, `coherence`): the bridge covers explicit finite data only.
