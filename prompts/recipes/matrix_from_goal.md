# Matrix computation from the goal

## When to use

- The goal states an identity, determinant or trace of explicit matrices (`!![…]` literals, `*`, `+`, transposes, `det`, `trace`), possibly with symbolic entries.
- Unlike `matrix_identity`, nothing is transcribed by hand. `goal.expr` already holds `lhs - rhs` as a Sage matrix (or a scalar for `det` and `trace`), read from the goal itself.
- Sage checks it is zero, and reports the actual difference with `matrix_term` when it is not. Lean proves it entry by entry with `norm_num`, or by the closed `det`/`trace` formula and `ring`.

## Template

Copy it to the project's `certificates/matrix_from_goal.sage` (or a more specific name), adapt the lines marked `EDIT`, keep the header, and run it with `sage_run file "certificates/<name>.sage"`.

```sage
# name: matrix_from_goal
# technique: matrix computation read from the goal, checked entrywise
# goal: an identity, determinant or trace of explicit matrices, written in the goal (!![…], *, ⁻¹, det, trace)
# description: Sage evaluates lhs - rhs from the goal itself; Lean proves it entry by entry or by the det/trace formula.
import re
SIMP = []  # EDIT: extra simp lemmas for norm_num, for example definitions of named matrices
e = goal.expr
assert e is not None, 'the goal has no symbolic form; transcribe the matrices with the matrix_identity recipe'
simp = f'norm_num [{", ".join(SIMP)}]' if SIMP else 'norm_num'
if hasattr(e, 'nrows'):
    # a matrix identity: lhs - rhs must be the zero matrix
    assert e.simplify_full() == 0, f'the identity is false: lhs - rhs = {matrix_term(e.simplify_full(), problem)}'
    proof = tactic(f'ext i j\nfin_cases i <;> fin_cases j <;> {simp}')
else:
    # a determinant or trace: lhs - rhs must simplify to 0; rewrite by the formula for the literal's size
    assert bool(e.simplify_full() == 0), f'the identity is false: lhs - rhs = {symbolic(e.simplify_full(), problem)}'
    literal = re.search(r'!!\[(.*?)\]', goal.text)
    assert literal, 'no !![…] literal in the goal; use the matrix_identity recipe'
    n = literal.group(1).count(';') + 1
    assert n in (2, 3), f'no closed formula for {n}×{n}; expand with Matrix.det_succ_row_zero'
    kind = 'det' if 'det' in goal.text else 'trace'
    formula = {('det', 2): 'Matrix.det_fin_two_of', ('det', 3): 'Matrix.det_fin_three',
               ('trace', 2): 'Matrix.trace_fin_two_of', ('trace', 3): 'Matrix.trace_fin_three_of'}[kind, n]
    proof = tactic(f'rw [{formula}]\nring')
```

## Worked example

```lean
example : !![(2 : ℚ), 1; 1, 1] * !![1, -1; -1, 2] = 1 := by
  sage_run file "certificates/matrix_from_goal.sage"
-- replacement:
--   ext i j
--   fin_cases i <;> fin_cases j <;> norm_num

example (c : ℚ) : Matrix.det !![(1 : ℚ), c; 0, 1] = 1 := by
  sage_run file "certificates/matrix_from_goal.sage"
-- replacement:
--   rw [Matrix.det_fin_two_of]
--   ring
```

## Failure modes

- **"the identity is false: lhs - rhs = !![…]":** the statement is wrong; the rendered difference shows which entries disagree.
- **"the goal has no symbolic form":** the matrices are named (`σ₁`, `γ 0`), not literals. Use `matrix_identity` and transcribe them, or unfold the names first and add their definitions to `SIMP`.
- **`norm_num` leaves an entry:** add the lemmas it needs to `SIMP` (for example `Matrix.mul_apply`, `Fin.sum_univ_succ`), or follow with `ring`.
- **Larger than 3×3 for `det`:** expand with `Matrix.det_succ_row_zero` and `Fin.sum_univ_succ`.
