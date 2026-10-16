# Test fallback

## When to use

- Only when no certificate is feasible: the recipe selection of `prompts/certify.md` ran and every matching recipe
  failed, or the claim quantifies over a dimension, a space or a function (rank-nullity for every `A`, a statement
  in every dimension `n`). A certificate always comes first; a test never stands in for one.
- The claim is a theorem (proved in mathlib, or by hand) or a definition of type `Prop` (stated, unproved), with
  universal binders. `sage_test c file "<copy>.sage"` opens the binders and runs the script, which chooses
  instances: values for every binder, each with a tactic block the kernel checks by computation (`norm_num`,
  `decide`, or a recipe's own emitter), or an oracle verdict Sage evaluates exactly or in `RealIntervalField(53)` or
  finer when Lean cannot state the instance.
- Lean states each instance with `veriphy_instance% c v₁ …`, from the statement and never the proof, and rejects a
  proof that depends on `c`, directly or through this module's declarations. A run needs three accepted instances,
  one an edge case (zero, one, the identity, a singular matrix, `n = 0`).
- The result has a level, and the report names it: `kernel-test` when every accepted instance is kernel-checked,
  `oracle-test` when some are Sage's alone. `#veriphy_levels <prefix>` lists every claim's level (`certificate`,
  `kernel-test`, `oracle-test`, `none`).

## Template

Copy it to the project's `.veriphy/certificates/<claim>_test.sage`, adapt the lines marked `EDIT`, keep the header,
and run it with `sage_test <claim> file "<claim>_test.sage"`.

```sage
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
```

`default_cases(universal, Sampler(SEED))` builds instances for scalar binders (`ℕ`, `ℤ`, `ℚ`, `ℝ`) and for matrices
`Matrix (Fin a) (Fin b) K` whose sizes are numerals or earlier `ℕ` binders, edge cases first. For other binder types,
list `CASES` by hand, or build `instances` directly with `kernel_instance(…, proof=…, edge=…)` and
`oracle_instance(…, lhs=…, rhs=…, relation=…)`.

## Worked example

```lean
theorem traceDouble (n : ℕ) (A : Matrix (Fin n) (Fin n) ℚ) : Matrix.trace (A + A) = 2 * Matrix.trace A := by
  rw [Matrix.trace_add]; ring

-- with PROOF = 'simp [Matrix.trace, Fin.sum_univ_succ]\nall_goals ring': n = 0 and the zero matrix, then samples
sage_test traceDouble file "trace_double_test.sage"
-- Sage-free replacement: an `example : veriphy_instance% traceDouble (0) (…) := by …` per instance, and
-- attribute [veriphy_tested kernel_test 4 0] traceDouble
```

Commit the replacement in place of the `sage_test` command: it builds without Sage, rechecks every kernel instance,
and records the level. The run also writes `.veriphy/tests/<claim>.json` (the instances, the seed, Sage's version);
commit it too. `sage -python -m veriphy.certificates tests` lists the records, and `tests --rerun <claim>` reruns
their oracle instances.

## Failure modes

- **"a test needs 3 accepted instances, one of them an edge case":** the message lists every rejected instance with
  its reason; fix the proofs, or add instances and an edge case.
- **"the proof depends on `c` …, so it tests nothing":** an instance's proof used the claim itself, or a lemma of this
  module built on it; prove the instance by computation.
- **"the block does not close the instance":** the tactic block is too weak for that instance.
- **"Sage refutes `c` at …":** an oracle instance contradicts the claim; the claim is false there, and the report is
  `statement-suspect`.
- **"floating-point values cannot decide it":** evaluate exactly, or in `RealIntervalField(53)` or finer.
- **"no default instances for the binder …":** the binder's type is not one `default_cases` builds; list `CASES` by
  hand.
