# Operator identities

## When to use

- **Matrix operators:** commutators of explicit matrices over ℂ (Pauli and spin matrices, gamma matrices, truncated
  ladder operators). `operator_relations(matrices, names)` solves `[Xᵢ, Xⱼ] = Σ cₖ Xₖ` over ℚ(i) and proves each
  relation entrywise. Gamma-matrix identities (traces, contractions, Fierz) have their own tools:
  `clifford_facts`, `fierz_fact`, checked by the kernel over ℤ[i].
- **Differential operators:** identities between operators built from multiplications by polynomials and partial
  derivatives, applied to a test function `ψ`. `Coordinates(n)` gives `partial(i)` and `multiplication(e)`; operators
  compose with `*`, add with `+` and `-`, and `commutator(a, b)`. `operator_identity(lhs, rhs, coordinates)` checks the
  identity in Sage on a symbolic `ψ` and proves `(lhs ψ) x = (rhs ψ) x` in Lean: derivatives of products by `simp`
  with `fun_prop` side conditions, `ring` to close. One variable uses `deriv`; several use
  `fderiv ℝ f y (Pi.single j 1)` and mathlib's symmetry of second derivatives, so second-order identities in several
  variables need `ContDiff ℝ 2 ψ`.

## Template

Copy it to the project's `.veriphy/certificates/operator_identity.sage` (or a more specific name), adapt the lines
marked `EDIT`, keep the header, and run it with `sage_run file "<name>.sage"`.

```sage
# name: operator_identity
# technique: operator identities: matrix commutators entrywise, differential operators on a test function
# goal: a commutator or composition of explicit matrices, or of differential operators applied to a function ψ
# description: Sage computes the commutators; Lean proves matrix ones entrywise and differential ones by derivative lemmas.
MATRICES = None  # EDIT: matrices over ℚ(i) (Sage), for the commutators [Xᵢ, Xⱼ] of named Lean matrices
NAMES = None  # EDIT: their Lean names (definitions over ℂ), in the same order
PAIRS = None  # EDIT: the pairs (i, j) the goal states, or None for every i < j
COORDINATES = None  # EDIT: Coordinates(n) for differential operators in n variables
LHS = None  # EDIT: the left operator, from COORDINATES.partial(i), COORDINATES.multiplication(e), commutator(a, b)
RHS = None  # EDIT: the right operator
CLOSE = 'trivial'  # EDIT: the tactic closing the goal from the facts, e.g. 'simpa using hop'
if MATRICES is not None:
    facts = operator_relations(MATRICES, NAMES, PAIRS)
elif LHS is not None:
    facts = operator_identity(LHS, RHS, COORDINATES)
else:
    raise AssertionError('fill in MATRICES and NAMES, or COORDINATES, LHS and RHS, in a copy')
proof = steps(facts, tactic(CLOSE))
```

## Worked examples

```lean
-- with COORDINATES = Coordinates(1), LHS = commutator(d/dx, x), RHS = 1 and CLOSE = 'simpa using hop'
example (ψ : ℝ → ℝ) (hψ : ContDiff ℝ 1 ψ) (x : ℝ) : deriv (fun y => y * ψ y) x - x * deriv ψ x = ψ x := by
  sage_run file "canonical_commutator.sage"
```

`VeriphyTest/SageRun.lean` also proves `[L₁, L₂] = -L₃` for angular momentum in three variables, the Pauli
commutators and the truncated ladder operators.

## Failure modes

- **"fill in MATRICES …":** copy the template and fill in one kind of identity.
- **"the identity fails in Sage: the two sides differ by …":** the claimed operator identity is wrong; the difference,
  applied to `ψ`, is shown.
- **"operators in several variables are supported up to second order":** higher orders need the symmetry of higher
  derivatives; split the identity, or prove it in one variable.
- **"is not in the span of the matrices":** a commutator leaves the span; add the missing matrix.
- **An unsolved goal after `simp`:** the goal states the operators differently (a library definition, a
  `ContinuousLinearMap`); unfold them first. Library operators need their unfolding lemmas (for Physlib, the pack's
  rewrite entries such as `loweringCLM_eq`); operators without such lemmas need them proved first.
