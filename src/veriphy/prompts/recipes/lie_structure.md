# Lie structure

## When to use

- The goal is a fact about a Lie algebra **given by explicit matrices**:
  - a bracket of explicit matrices, `⁅!![…], !![…]⁆ = !![…]`;
  - bracket relations of named matrices, such as the table of 𝔰𝔩₂, `⁅h, e⁆ = 2 • e ∧ ⁅e, f⁆ = h`;
  - a matrix (a Casimir) commuting with each basis matrix;
  - a determinant or inverse of a mathlib Cartan matrix, `(CartanMatrix.E 8).det = 1`, `CartanMatrix.F₄⁻¹ = !![…]`.
- Sage does the Lie theory. `structure_constants(basis)` solves `⁅eᵢ, eⱼ⁆ = Σ cᵢⱼₖ eₖ` and reports the first
  pair whose bracket leaves the span; `killing_form`, `trace_form` and `casimir(basis, form)` give the invariant forms
  and the quadratic Casimir; `cartan_matrix`, `weyl_group_order` and `positive_roots` give root data in mathlib's
  conventions (`CartanMatrix.B`, `C` and `F₄` are the transposes of Sage's).
- Lean receives only finite identities: each relation is checked by the kernel (`VeriphyCheck.bracket_eq_of_check`,
  `commute_of_check`, `det_eq_of_lu_int`, `inv_eq_of_check`) over ℚ or ℤ, or entrywise over ℝ. A structure-constant
  table is checked for the Jacobi identity by `jacobi_certificate(table)` (`VeriphyCheck.jacobi_of_check`).

## Template

Copy it to the project's `.veriphy/certificates/lie_structure.sage` (or a more specific name), adapt the lines marked
`EDIT`, keep the header, and run it with `sage_run file "<name>.sage"`.

```sage
# name: lie_structure
# technique: Lie algebra facts of explicit matrices from Sage's Lie theory, each identity checked by Lean
# goal: ⁅A, B⁆ = C; bracket relations or commutations of named matrices (a conjunction); det or ⁻¹ of a CartanMatrix
# description: Sage computes structure constants, Casimirs or root data; the kernel or an entrywise proof checks each.
import re
BASIS = []  # EDIT: the basis matrices in Sage (matrix(QQ, [[...]])), when the goal names them by their definitions
NAMES = []  # EDIT: their Lean names, in the same order
CASIMIR = None  # EDIT: the Lean name of a matrix the goal says commutes with each matrix of NAMES
CARTAN = None  # EDIT: the Cartan type ('E8', 'F4') of a goal about CartanMatrix
CARRIER = 'ℚ'  # EDIT: the entries' type: ℚ or ℤ use the kernel checkers, ℝ an entrywise proof

text = goal.text if goal is not None else ''
conjuncts = text.count(' ∧ ') + 1
close = tactic('assumption' if conjuncts == 1 else 'refine ⟨' + ', '.join(['?_'] * conjuncts) + '⟩ <;> assumption')
limit = 0 if CARRIER in ('ℚ', 'ℤ') else 64
if CARTAN is not None:
    certificate = inverse_certificate() if '⁻¹' in text else det_certificate(cartan_matrix(CARTAN))
    proof = tactic('exact ' + str(certificate))
elif CASIMIR is not None:
    size = BASIS[0].nrows()
    proof = steps(commutation_facts(CASIMIR, NAMES, size=size, carrier=CARRIER, entrywise_limit=limit), close)
elif BASIS:
    index = {name: i for i, name in enumerate(NAMES)}
    pairs = [(index[a], index[b]) for a, b in re.findall(r'⁅(\S+), (\S+)⁆', text)]
    assert pairs, f'no bracket ⁅x, y⁆ of the names {NAMES} in the goal {text}'
    proof = steps(bracket_relations(BASIS, NAMES, pairs=pairs, carrier=CARRIER, entrywise_limit=limit), close)
else:
    residual = goal.expr if goal is not None else None
    assert residual is not None, 'the goal has no symbolic form; name the matrices in BASIS and NAMES'
    assert residual == 0, f'Sage finds the two sides differ by {residual}'
    if CARRIER in ('ℚ', 'ℤ'):
        proof = tactic('exact VeriphyCheck.bracket_eq_of_check (by decide +kernel)')
    else:
        proof = tactic('rw [Ring.lie_def]\next i j\nfin_cases i <;> fin_cases j <;> norm_num [Matrix.mul_apply, Fin.sum_univ_succ]')
```

## Worked examples

```lean
-- the template unedited: a bracket of explicit matrices
example : ⁅!![(0 : ℚ), 1; 0, 0], !![(0 : ℚ), 0; 1, 0]⁆ = !![(1 : ℚ), 0; 0, -1] := by
  sage_run file "lie_structure.sage"
-- replacement: exact VeriphyCheck.bracket_eq_of_check (by decide +kernel)

-- with BASIS = [e, f, h] as Sage matrices and NAMES = ['e', 'f', 'h']
example : ⁅h, e⁆ = 2 • e ∧ ⁅e, f⁆ = h := by
  sage_run file "lie_sl2.sage"
-- replacement:
--   have hb_2_0 : ⁅h, e⁆ = 2 • e := VeriphyCheck.bracket_eq_of_check (by decide +kernel)
--   have hb_0_1 : ⁅e, f⁆ = h := VeriphyCheck.bracket_eq_of_check (by decide +kernel)
--   refine ⟨?_, ?_⟩ <;> assumption

-- with CARTAN = 'E8': an LU factorization over ℚ, checked by the kernel
example : (CartanMatrix.E 8).det = 1 := by
  sage_run file "cartan_e8.sage"
```

## Failure modes

- **"the basis is not closed under the bracket: ⁅e0, e1⁆ is not in its span":** the matrices do not span a Lie
  algebra. Add the bracket the message names to the basis, or check the matrices.
- **"has non-rational structure constants":** the basis has irrational constants (Gell-Mann's `λ₈` direction carries
  `√3`). Choose a basis with rational constants (for `su(n)`, `i(Eⱼⱼ - Eₖₖ)`, `Eⱼₖ - Eₖⱼ`, `i(Eⱼₖ + Eₖⱼ)`), or work
  over a number field.
- **"the invariant form is degenerate":** the Killing form of an algebra that is not semisimple. Pass another
  invariant form to `casimir`, such as the trace form of a faithful representation.
- **"the matrix needs pivoting":** a leading minor vanishes; reorder the rows and columns (a Cartan matrix never
  needs it).
- **An abstract Lie algebra** (a `LieAlgebra` instance with no matrices in the goal, a quotient, a free Lie algebra)
  is out of scope: the bridge needs explicit matrices. Prove such goals with mathlib's Lie theory directly.
- **Brackets on matrix Lie subalgebras** (`⁅x, y⁆` for `x y : L`) translate through the underlying matrices; mathlib
  makes the associative Lie ring a local instance, so state such goals after
  `attribute [local instance 100] LieRing.ofAssociativeRing`, as mathlib and Physlib do.
