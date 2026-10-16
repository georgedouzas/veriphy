# Design

## Context

Veriphy closes a goal with `sage_run`: a Sage script computes the data of a certificate, emits a Lean tactic block,
and the kernel checks the block, which is committed as the Sage-free replacement. A recipe is a tested template for
one goal shape. The book *Kaluza-Klein Theories and Coset Space Dimensional Reduction* requires every claim to be
checked through Veriphy. Its pilot chapter (linear algebra) proved all 527 claims in Lean but closed only 39 % of the
404 theorems through a recipe. The rest fell into two groups:

- computational claims whose shape no recipe or translation covers (dimension counts, ranks, spans, vector
  evaluations, signatures, integrals, polynomial identities), about 150 theorems;
- claims with no computational core (statements in arbitrary dimension, structural facts, definitions), about 95
  theorems, where no Sage computation can supply certificate data.

The first group needs recipes. The second needs a different kind of check, because a certificate does not exist.

## Goals / Non-Goals

**Goals:**

- Every claim the book makes has a Veriphy check, at a stated level.
- A test never passes for a proof: every record names its level, and the levels are ordered.
- The measured linear-algebra gaps close with recipes, so a certificate replaces a test wherever one is feasible.

**Non-Goals:**

- Proving theorems in arbitrary dimension by computation. Their proofs stay mathlib proofs, and Veriphy adds a
  test of the formal statement.
- Formalising Sylvester's law of inertia. The `signature` recipe certifies an explicit diagonalisation, and the
  invariance claim is tested.
- The pre-pilot gaps that linear algebra does not exercise. They are designed when the chapters that need them are
  measured.

## Decisions

### D1. Three levels, in order

| Level | What is checked | Replayable without Sage |
|---|---|---|
| `certificate` | a recipe found the data, the kernel checked the proof of the claim | yes |
| `kernel-test` | the kernel checked the claim at instances chosen by Sage, each by computation alone | yes |
| `oracle-test` | Sage evaluated the claim at instances, in exact or interval arithmetic | no (the record is kept) |

A claim gets the highest level that is feasible. The fallback applies only when no recipe applies, and the recipe
document says how to establish that (the recipe selection in `prompts/certify.md` ran and failed, or the goal is
universally quantified over a dimension, a space or a function).

### D2. `sage_test` is a command on a proposition

```lean
theorem rank_nullity (A : Matrix (Fin m) (Fin n) ℚ) : A.rank + finrank ℚ (ker A.mulVecLin) = n := …

sage_test rank_nullity file "rank_nullity_test.sage"
```

The target is a constant whose type is a proposition (a theorem) or a definition of type `Prop`. Lean opens its
universal binders as a telescope and serializes the binders and the body as a problem, the way existential goals are
serialized today. The script assigns `instances`, a list of instances. Each instance gives every binder a value as
Lean text and either a `proof` (a tactic block) or an `oracle` verdict with the evaluation it made.

For a `proof` instance, Lean elaborates the values at the binder types, instantiates the body and runs the block.
The instance is accepted only when the block closes the goal with the standard axioms, and the proof term does not
mention the target constant. The second condition makes the test independent of the proof under test: an instance
checked through `rank_nullity` itself would test nothing.

The Sage-free replacement is the list of accepted instances as `example` commands, followed by the attribute
`veriphy_tested` on the target, which records the level and the counts. An `oracle` instance cannot be replayed
without Sage, so it is written to the test record (D4) and counted in the attribute.

### D3. Choice of instances

The script chooses the instances, since only it knows the domain. The template provides a seeded sampler and the edge
cases of the common binder types (zero, one, the identity, a singular matrix, a degenerate dimension). A run needs at
least three accepted instances, of which at least one edge case, or it fails with the list of rejected instances and
the reasons. The seed is part of the record.

### D4. The test record

Every `sage_test` run writes `.veriphy/tests/<target>.json` with the target, its statement, the level, the seed, the
Sage version, the script's hash and every instance with its values, its kind (`kernel` or `oracle`) and its verdict.
The record is committed with the project. `python -m veriphy.certificates tests` lists the records and their levels,
and `--rerun <target>` reruns the oracle part. An oracle evaluation uses exact arithmetic, or interval arithmetic of
at least 53 bits when no exact form exists. Floating-point comparison is rejected.

### D5. Linear-algebra recipes share one toolkit module

A new toolkit module `_linear.py` holds the Sage side: echelon forms, pivots, kernel and span bases, coordinates,
rank factorisations, `LDLᵀ` congruences and the points where linearity fails. Its emitters write the Lean side
through existing primitives (`matrix_from_goal` determinants, `ideal_membership` cofactors, `norm_num`) and a small
Lean helper file `Veriphy/Kit/Linear.lean` with the packaging lemmas (span of an echelon family, rank bounds from a
minor and a factorisation, independence from a non-zero minor).

- `dimension`: `finrank` of a span is `finrank_span_eq_card` plus independence. `finrank` of a kernel is rank-nullity
  plus a surjectivity witness. Sums and intersections use `Submodule.finrank_mono` and
  `Submodule.eq_of_le_of_finrank_eq`. `finrank` of `Fin n → K`, `Matrix`, `TensorProduct` and `Module.Dual` reduce by
  the product formulas.
- `matrix_rank`: a non-singular `r × r` minor gives `≥ r`, a factorisation `A = B C` with inner size `r` gives `≤ r`.
- `independence`: independence from a non-zero minor (`Matrix.linearIndependent_rows_of_det_ne_zero`), dependence
  from an explicit relation, span equality from coordinates in both directions.
- `nonlinearity`: `rintro ⟨f, hf⟩`, then `map_add`, `map_smul` or `map_zero` at the points Sage found, then `norm_num`.
- `signature`: the congruence `Pᵀ S P = D` and `det P ≠ 0` by `matrix_from_goal`, the sign counts by `norm_num`.

### D6. Vectors and polynomials in the translation

`![a, b, c]` becomes a column vector of the matrix IR that `matrix_from_goal` already reads. `A *ᵥ v`, `v ᵥ* A`,
`v ⬝ᵥ w`, `vecMulVec u v` and `diagonal v` become matrix products and diagonal matrices of that IR. A named matrix
whose definition unfolds to a literal (by `delta` and `simp only` of the definition) is read through its literal.
`Polynomial` over a translated field becomes a polynomial ring in a generator for `X`, with `derivative`, `eval` and
`natDegree` mapped to Sage's. Emitted proofs for vectors use `funext` with `Fin` cases and `norm_num [Matrix.mulVec,
dotProduct, Fin.sum_univ_succ]`.

### D7. Side relations in `matrix_from_goal`

The option `relations=[…]` names Lean lemmas of the form `lhs = rhs` (`Real.cosh_sq_sub_sinh_sq`, `Real.sq_sqrt`,
`Real.cos_sq_add_sin_sq`). Sage reduces every entry of `lhs - rhs` of the goal modulo the ideal the relations
generate, and emits each entry as `linear_combination` of the relation lemmas with the cofactors. This covers boosts,
rotations and matrices with square roots. The template's other limits (`4 × 4` determinants by Laplace expansion,
products with `ᵀ`, symbolic entries closed by `ring1`, traces) are lifted in the same template.

### D8. `definite_integral`

For `∫ x in a..b, f x = v`, Sage finds an antiderivative `F`. The emitter proves `HasDerivAt F (f x) x` with the
`derivative` recipe's `has_deriv_at`, applies `intervalIntegral.integral_eq_sub_of_hasDerivAt` (with continuity of
`f` by `fun_prop`), and evaluates `F b - F a` with the `transcendental_rewrite` table and `norm_num`. Rescaled
arguments use `intervalIntegral.integral_comp_mul_left`.

### D9. The replacement only after the kernel accepted it

`sage_run` and `sage_test` report `Sage-free replacement` only after the block closed the goal and the axiom check
passed. A failed block reports the combined error and no replacement.

### D10. Lean builds run one at a time

The development machine has 16 GB and a Lean file importing mathlib uses about 4.5 GB. Every `lake build` and
`lake env lean` in this change runs under a lock, so parallel work never starts two Lean processes at once.

## Risks / Trade-offs

- A test with three instances can pass a wrong statement. The record shows the instances, the level is printed next
  to the claim, and a certificate replaces the test whenever a recipe appears for the shape.
- The independence condition of D2 (the proof term does not mention the target) can be circumvented through a lemma
  that wraps the target. The check walks the constants of the proof term transitively through the current module's
  declarations, and stops at imported modules.
- Oracle records age when Sage changes. The record names the Sage version, and `--rerun` checks it again.

## Migration Plan

New commands and recipes only. Existing projects are unchanged. The book pins the branch, then the release.

## Open Questions

None at this point. The next chapters' measurements will extend the recipe list.
