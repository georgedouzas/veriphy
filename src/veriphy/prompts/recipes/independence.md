# Linear independence and spans

## When to use

- The goal is `LinearIndependent K v` or `¬ LinearIndependent K v` for an explicit family `v = ![![…], …]`, or an
  equality of spans: `span K (range v) = span K (range w)`, or `span K (range v) = ker A.mulVecLin`.
- Sage finds a non-singular minor (independence, through `Veriphy.Linear.linearIndependent_of_minor`), a relation
  (dependence, through `Fintype.not_linearIndependent_iff`), or the coordinates of every generator in the other family
  (span equality, both inclusions). For a kernel, a kernel vector's coordinates are read off the rows of a
  non-singular minor and checked by `linarith` from the kernel equations.

## Template

Copy it to the project's `.veriphy/certificates/independence.sage` (or a more specific name), adapt the lines marked
`EDIT`, keep the header, and run it with `sage_run file "<name>.sage"`.

```sage
# name: independence
# technique: linear independence from a non-singular minor, dependence from a relation, spans from coordinates
# goal: LinearIndependent K v, ¬ LinearIndependent K v, or span K (range v) = span K (range w) or = ker A.mulVecLin
# description: Sage finds the minor, the relation or the coordinates; Lean checks them by evaluation.
VECTORS = None  # EDIT: the family v as the goal states it, as [[1, 2, 0], [0, 1, 1]]
OTHER = None  # EDIT: for span (range v) = span (range w), the family w
KERNEL = None  # EDIT: for span (range v) = ker A.mulVecLin, the matrix A, as [[1, 1, 1]]
FIELD = 'ℚ'  # EDIT: the scalars of the goal
assert VECTORS is not None, 'fill in VECTORS (and OTHER or KERNEL for a span equality) in a copy'
if OTHER is not None or KERNEL is not None:
    kernel = matrix(QQ, KERNEL) if KERNEL is not None else None
    proof = tactic(span_proof(VECTORS, other=OTHER, kernel_of=kernel, field=FIELD))
else:
    proof = tactic(independence_proof(VECTORS, negated=goal.text.lstrip().startswith('¬')))
```

## Worked examples

```lean
example : LinearIndependent ℚ ![![(1 : ℚ), 2, 0], ![0, 1, 1]] := by
  sage_run "proof = tactic(independence_proof([[1, 2, 0], [0, 1, 1]]))"

-- dependent: the relation 2 v₀ - v₁ = 0
example : ¬ LinearIndependent ℚ ![![(1 : ℚ), 2], ![2, 4]] := by
  sage_run "proof = tactic(independence_proof([[1, 2], [2, 4]], negated=True))"

example : Submodule.span ℚ (Set.range ![![(-1 : ℚ), 1, 0], ![-1, 0, 1]]) =
    LinearMap.ker (Matrix.mulVecLin !![(1 : ℚ), 1, 1]) := by
  sage_run "proof = tactic(span_proof([[-1, 1, 0], [-1, 0, 1]], kernel_of=matrix(QQ, [[1, 1, 1]])))"
```

## Failure modes

- **"the family is dependent: … is a relation" / "the family is linearly independent":** the claim is false; the
  message shows the relation or that none exists.
- **"… is not in the span of the family":** the spans differ.
- **"the family does not span the kernel":** a generator is outside the kernel, or the family is too small.
