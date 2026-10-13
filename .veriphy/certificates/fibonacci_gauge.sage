# name: fibonacci_gauge
# technique: fusion rules, pentagon and hexagon equations over number fields, gauge transformations
# goal: FusionData.IsFusion or IsBraidedFusion of explicit data (RepData.toData E ζ), or FusionData.GaugeRelated
# description: Sage builds and checks the data and finds gauges; the kernel checks the equations on coefficient lists.
REFERENCE = fibonacci()
TARGET = gauge_transform(REFERENCE, {(1, 1, 1): 2})  # the goal's F-symbols, in the gauge u^{ττ}_τ = 2
KIND = 'gauge'  # EDIT: 'fusion' (IsFusion or IsBraidedFusion) or 'gauge' (GaugeRelated REFERENCE TARGET)
BRAIDED = False  # EDIT: False for IsFusion (the pentagons only)
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
