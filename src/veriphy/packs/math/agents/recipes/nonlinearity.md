# Maps that are not linear

## When to use

- The goal is `¬ ∃ f : K →ₗ[K] K, ∀ x, f x = g x`, or the bilinear `¬ ∃ f : V →ₗ[K] W →ₗ[K] K, ∀ x y, f x y = g x y`.
- Sage tests `g` for `g 0 = 0`, homogeneity and additivity at small rational points; Lean specialises the failing law
  of `f` (`map_zero`, `map_smul`, `map_add`) at those points, rewrites by the hypothesis and computes. A bilinear map
  is refuted at `f 0 0 = 0`.

## Template

Copy it to the project's `.veriphy/certificates/nonlinearity.sage` (or a more specific name), adapt the lines marked
`EDIT`, keep its `SCRIPT` declaration, and run it with `veriphy certify "<name>.sage"`.

```sage
SCRIPT = {
    'name': 'nonlinearity',
    'serves': 'certify',
    'technique': 'a failure of map_zero, map_smul or map_add at points Sage finds',
    'goal': '¬ ∃ f : K →ₗ[K] K, ∀ x, f x = g x, or the bilinear ¬ ∃ f : V →ₗ[K] W →ₗ[K] K, ∀ x y, f x y = g x y',
    'description': 'Sage tests the linear laws on g; Lean specialises the failing law of f at the points and computes.',
    'inputs': {},
}

MAP = None  # EDIT: g as a Python function of Sage values, as lambda x: x ** 2 (two arguments for a bilinear map)
ARITY = 1  # EDIT: 2 for a bilinear map (refuted by f 0 0 = 0)


def run(goal, inputs):
    assert MAP is not None, 'fill in MAP in a copy'
    proof = tactic(nonlinearity_proof(MAP, ARITY))
    return found(proof)
```

## Worked examples

```lean
example : ¬ ∃ f : ℝ →ₗ[ℝ] ℝ, ∀ x, f x = x ^ 2 := by
  veriphy certify "proof = tactic(nonlinearity_proof(lambda x: x ** 2))"

example : ¬ ∃ f : (Fin 2 → ℝ) →ₗ[ℝ] (Fin 2 → ℝ) →ₗ[ℝ] ℝ, ∀ x y, f x y = x 0 * y 0 + 1 := by
  veriphy certify "proof = tactic(nonlinearity_proof(lambda x, y: 1, 2))"
```

## Failure modes

- **"the map passes additivity and homogeneity at every test point":** `g` may be linear; check the claim.
- **"the bilinear map vanishes at zero":** only a non-zero value at zero is certified for bilinear maps; refute
  additivity in one argument by hand with `LinearMap.map_add₂`.
