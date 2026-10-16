# Dimensions of subspaces

## When to use

- The goal is `Module.finrank K V = n` with `V` the span of explicit vectors, an intersection of two such spans, the
  kernel of a functional, or a product space (`Fin n → K`, `Matrix`, `⊗`).
- A span's dimension is its rank: an independent family by `Veriphy.Linear.finrank_span_of_minor`, a dependent one
  after rewriting its span to the span of an echelon basis. An intersection's dimension comes from a basis of it
  (Sage) and an independent family spanning the sum, through the dimension formula
  (`Veriphy.Linear.finrank_inf_of_bounds`). A functional's kernel has codimension one given a vector it sends to `1`
  (`Veriphy.Linear.finrank_ker_add_one`). Product spaces close by the product formulas.

## Template

Copy it to the project's `.veriphy/certificates/dimension.sage` (or a more specific name), adapt the lines marked
`EDIT`, keep the header, and run it with `sage_run file "<name>.sage"`.

```sage
# name: dimension
# technique: finrank of spans, intersections, kernels of functionals and product spaces
# goal: Module.finrank K V = n, V a span of explicit vectors, an intersection of two spans, a kernel, or a product space
# description: Sage computes ranks and bases; Lean uses independence from minors, the dimension formula, rank-nullity.
KIND = 'span'  # EDIT: 'span', 'intersection', 'kernel' (of a functional) or 'product' (Fin n → K, Matrix, ⊗, Dual)
VECTORS = None  # EDIT: for 'span', the family as the goal states it
FIRST, SECOND = None, None  # EDIT: for 'intersection', the two independent families
FUNCTIONAL, WITNESS = None, None  # EDIT: for 'kernel', the Lean texts of the functional and of a vector it sends to 1
FIELD = 'ℚ'  # EDIT: the scalars of the goal
if KIND == 'span':
    assert VECTORS is not None, 'fill in VECTORS in a copy'
    proof = tactic(span_dimension_proof(VECTORS, FIELD))
elif KIND == 'intersection':
    assert FIRST is not None and SECOND is not None, 'fill in FIRST and SECOND in a copy'
    proof = tactic(intersection_dimension_proof(FIRST, SECOND, FIELD))
elif KIND == 'kernel':
    assert FUNCTIONAL is not None and WITNESS is not None, 'fill in FUNCTIONAL and WITNESS in a copy'
    proof = tactic(
        f'have h := Veriphy.Linear.finrank_ker_add_one ({FUNCTIONAL}) ({WITNESS}) (by simp)\n'
        'simp [Module.finrank_matrix, Module.finrank_fin_fun] at h\n'
        'omega'
    )
else:
    proof = tactic('simp [Module.finrank_tensorProduct, Module.finrank_matrix, Module.finrank_fin_fun]')
```

## Worked examples

```lean
example : Module.finrank ℚ ↥(Submodule.span ℚ (Set.range ![![(1 : ℚ), 2, 0], ![0, 1, 1], ![1, 3, 1]])) = 2 := by
  sage_run "proof = tactic(span_dimension_proof([[1, 2, 0], [0, 1, 1], [1, 3, 1]]))"

-- the kernel of the trace, with a matrix of trace one (KIND = 'kernel')
example : Module.finrank ℝ ↥(LinearMap.ker (Matrix.traceLinearMap (Fin 3) ℝ ℝ)) = 8 := by
  sage_run file "trace_kernel.sage"
```

## Failure modes

- **"both families must be independent":** for an intersection, reduce each family to a basis first (the
  `independence` recipe finds the relations).
- **The kernel step stays open:** the witness is not sent to `1`, or the domain's dimension is not a product formula;
  state `finrank` of the domain first.
