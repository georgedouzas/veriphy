# name: test_fallback
# technique: test a claim no recipe certifies, at instances the kernel checks by computation (or Sage evaluates)
# goal: sage_test c file "<copy>.sage", for a theorem or a definition of type Prop with universal binders
# description: the script picks seeded instances with edge cases; Lean checks each one, independently of the claim.
SEED = 0  # EDIT: the sampler's seed, kept in the test record
PROOF = None  # EDIT: the tactic block proving the claim at one instance by computation, as 'simp [Matrix.trace]'
CASES = None  # EDIT: the instances as ([values as Lean text], edge?) pairs; None for default_cases(universal, …)
assert PROOF is not None, 'fill in PROOF (and CASES, unless the default instances fit the binders) in a copy'
cases = CASES if CASES is not None else default_cases(universal, Sampler(SEED))
instances = [kernel_instance(*values, proof=PROOF, edge=edge) for values, edge in cases]
