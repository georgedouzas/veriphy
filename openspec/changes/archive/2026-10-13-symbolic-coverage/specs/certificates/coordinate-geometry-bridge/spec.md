# Spec Delta

## Purpose

Lets scripts use SageManifolds to compute Christoffel symbols, curvature, Ricci tensors, Killing equations, differential forms and tensor contractions in coordinates, and prove each component in Lean against coordinate definitions. Neither mathlib nor Physlib currently provides those definitions in coordinates.

## ADDED Requirements

### Requirement: Reference coordinate definitions
Veriphy SHALL ship, as a recipe asset that a project copies into `.veriphy/lean/`, a Lean file defining these for a metric given as a matrix of functions of coordinates `Fin n → ℝ`:
- Christoffel symbols of the second kind;
- the Riemann and Ricci tensors and the scalar curvature;
- the Killing equation.

#### Scenario: Definitions present
- **WHEN** a project copies the asset
- **THEN** it can state `christoffel g i j k x`, `ricci g i j x` and `killing g X` for an explicit metric `g`

### Requirement: Definitions use mathlib only
The reference definitions SHALL be stated through partial derivatives and the inverse metric with mathlib's `deriv` and `Matrix` API only, so they need no Veriphy import and can be proposed upstream.

#### Scenario: Copying the definitions
- **WHEN** a project copies the asset into its sources
- **THEN** it builds against mathlib alone, with no `sorry`

### Requirement: Components checked one by one
The toolkit SHALL compute, with SageManifolds, each requested component for an explicit metric, and emit a Lean proof that the component defined by the reference file equals Sage's expression at an arbitrary point. The proof combines:
- unfolding;
- the partial-derivative proof terms;
- the inverse-metric identity, proved as a matrix identity with its determinant nonzero as a domain condition;
- `field_simp` and `ring`.

#### Scenario: Christoffel symbol of the 2-sphere
- **WHEN** the metric is `diag(1, sin² θ)` in coordinates `(θ, φ)`
- **THEN** the script emits a proof that `Γ^θ_φφ = -sin θ cos θ` at every point where `sin θ ≠ 0`

#### Scenario: Flat metric
- **WHEN** the metric is the Minkowski matrix in Cartesian coordinates
- **THEN** every Christoffel symbol is proved to be `0`

### Requirement: Geometry recipe
The recipe set SHALL include a `coordinate_geometry` recipe covering metrics, Christoffel symbols, curvature components, Ricci flatness and Killing vectors in coordinates. Its failure modes SHALL include:
- metrics whose determinant vanishes at the point;
- components too large to close by `ring` (then split per term);
- goals stated with the abstract manifold API, which are out of scope for the bridge.

#### Scenario: Killing vector
- **WHEN** the goal states that `∂_φ` is a Killing vector of the 2-sphere metric in coordinates
- **THEN** the template proves each component of the Killing equation

### Requirement: Differential forms in coordinates
The reference asset SHALL define differential forms on coordinates `Fin n → ℝ` as alternating component functions, together with the exterior derivative, the wedge product, and the Hodge star for a given metric. The toolkit SHALL compute with SageManifolds' `DiffForm` and emit componentwise proofs of claimed identities (`d (d ω) = 0` for an explicit `ω`, Maxwell's equations as `dF = 0` and `d⋆F = J`, closedness and exactness with an explicit primitive).

#### Scenario: Exact form with primitive
- **WHEN** the goal states that an explicit 1-form on ℝ³ is exact
- **THEN** the script finds a primitive with Sage and emits componentwise proofs that its exterior derivative is the form

### Requirement: Tensor contractions
The toolkit SHALL contract explicit tensors given by component arrays (index positions recorded, metric for raising and lowering), compute with Sage, and emit componentwise proofs. With the `physlib` pack active, it SHALL read and render Physlib's tensor index notation through the pack's entries.

#### Scenario: Electromagnetic invariant
- **WHEN** a script computes `F_{μν} F^{μν}` for an explicit field-strength matrix in Minkowski coordinates
- **THEN** it emits a proof that the contraction equals `2 (B² - E²)` in the goal's sign convention
