# name: nonlinearity
# technique: a failure of map_zero, map_smul or map_add at points Sage finds
# goal: ¬ ∃ f : K →ₗ[K] K, ∀ x, f x = g x, or the bilinear ¬ ∃ f : V →ₗ[K] W →ₗ[K] K, ∀ x y, f x y = g x y
# description: Sage tests the linear laws on g; Lean specialises the failing law of f at the points and computes.
MAP = None  # EDIT: g as a Python function of Sage values, as lambda x: x ** 2 (two arguments for a bilinear map)
ARITY = 1  # EDIT: 2 for a bilinear map (refuted by f 0 0 = 0)
assert MAP is not None, 'fill in MAP in a copy'
proof = tactic(nonlinearity_proof(MAP, ARITY))
