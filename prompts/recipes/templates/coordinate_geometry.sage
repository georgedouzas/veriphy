# name: coordinate_geometry
# technique: metrics, Christoffel symbols, Killing vectors, exact forms and contractions in coordinates
# goal: a statement about CoordinateGeometry.christoffel, IsKilling or extDeriv for an explicit metric or form
# description: SageManifolds computes the components; Lean proves them from the CoordinateGeometry asset's definitions.
METRIC = None  # EDIT: the metric's matrix (Sage) in the coordinates x0, x1, … (from coordinates(n))
NAME = None  # EDIT: the Lean name of the metric's definition, unfolded by the proofs
KIND = 'christoffel'  # EDIT: 'christoffel' (one component), 'killing' (a Killing vector), or 'exact' (a primitive)
FORM = None  # EDIT: for 'exact', the components of the 1-form (Sage, in the coordinates)
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
