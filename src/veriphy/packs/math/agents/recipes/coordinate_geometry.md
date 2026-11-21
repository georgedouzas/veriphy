# Coordinate geometry

## When to use

- The goal is about a **metric given in coordinates** (a family of component functions on `Fin n → ℝ`), stated with
  the definitions of the `CoordinateGeometry` asset: `christoffel g k i j x`, `riemann`, `ricci`,
  `scalarCurvature`, `lieMetric` and `IsKilling`, or about differential forms with `extDeriv`, `wedge` and `hodge`.
- Copy the asset into the project with
  `sage -python -m veriphy layers agents copy assets/VeriphyAssets/CoordinateGeometry` and declare the `VeriphyAssets`
  library (see the user guide). It imports mathlib only: partial derivatives are `deriv` along `Function.update`, the inverse metric is
  mathlib's `Matrix.inv`.
- SageManifolds computes the components (`christoffel_symbols(metric)`). Lean proves each component from the
  definitions: the inverse metric as a matrix identity (its determinant nonzero by a hypothesis such as
  `Real.sin (x 0) ≠ 0`), the partial derivatives by `simp` with derivative lemmas, then `field_simp` and `ring`.
  A constant metric's symbols vanish by `simp`. Exact 1-forms get a primitive from Sage (`primitive(form)`, which
  checks closedness first). Contractions of explicit arrays expand by `simp` and close by `ring`
  (`field_invariant` computes `F_μν F^μν` to compare).

## Template

Copy it to the project's `.veriphy/certificates/coordinate_geometry.sage` (or a more specific name), adapt the lines
marked `EDIT`, keep its `SCRIPT` declaration, and run it with `veriphy certify "<name>.sage"`.

```sage
SCRIPT = {
    'name': 'coordinate_geometry',
    'serves': 'certify',
    'technique': 'metrics, Christoffel symbols, Killing vectors, exact forms and contractions in coordinates',
    'goal': 'a statement about CoordinateGeometry.christoffel, IsKilling or extDeriv for an explicit metric or form',
    'description': "SageManifolds computes the components; Lean proves them from the CoordinateGeometry asset's definitions.",
    'inputs': {},
}

METRIC = None  # EDIT: the metric's matrix (Sage) in the coordinates x0, x1, … (from coordinates(n))
NAME = None  # EDIT: the Lean name of the metric's definition, unfolded by the proofs
KIND = 'christoffel'  # EDIT: 'christoffel' (one component), 'killing' (a Killing vector), or 'exact' (a primitive)
FORM = None  # EDIT: for 'exact', the components of the 1-form (Sage, in the coordinates)


def run(goal, inputs):
    assert METRIC is not None or FORM is not None, 'fill in METRIC and NAME, or FORM, in a copy'
    if KIND == 'christoffel':
        print(christoffel_symbols(METRIC))
        proof = christoffel_proof(METRIC, metric=NAME, unfold=[NAME])
    elif KIND == 'killing':
        proof = killing_proof(unfold=[NAME])
    else:
        f = primitive(FORM)
        print('primitive:', f)
        proof = exact_form_proof(f, len(FORM))
    return found(proof)
```

## Worked examples

```lean
noncomputable def sphere : Fin 2 → Fin 2 → (Fin 2 → ℝ) → ℝ :=
  ![![fun _ => 1, fun _ => 0], ![fun _ => 0, fun x => Real.sin (x 0) ^ 2]]

-- with METRIC = matrix(SR, [[1, 0], [0, sin(x0)^2]]) and NAME = 'sphere'
example (x : Fin 2 → ℝ) (h : Real.sin (x 0) ≠ 0) :
    CoordinateGeometry.christoffel sphere 0 1 1 x = -(Real.sin (x 0) * Real.cos (x 0)) := by
  veriphy certify "sphere_christoffel.sage"

-- ∂_φ is a Killing vector of the sphere (KIND = 'killing')
example : CoordinateGeometry.IsKilling sphere ![fun _ => 0, fun _ => 1] := by
  veriphy certify "proof = killing_proof(unfold=['sphere'])"
```

`lean/VeriphyTest/SageRun.lean` also proves every Christoffel symbol of Minkowski space zero, an exact 1-form on ℝ³ with
its primitive, and `F_μν F^μν = 2 (B² - E²)`.

## Failure modes

- **"fill in METRIC and NAME, or FORM":** copy the template and fill them in.
- **"the metric is degenerate":** its determinant vanishes identically; a determinant vanishing only at some points
  needs a hypothesis excluding them (`Real.sin (x 0) ≠ 0` on the sphere), which `field_simp` uses.
- **A component that `ring` leaves open:** large components (curvature of a generic metric) close better term by term;
  state intermediate facts for the Christoffel symbols first, then the curvature from them.
- **"the form is not closed":** no primitive exists; the message names the coordinates.
- **Goals with mathlib's abstract manifold API** (`ModelWithCorners`, `TangentBundle`) are out of scope: the bridge
  works in a single chart, on `Fin n → ℝ`.
