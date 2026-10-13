# Matrix normal forms

## When to use

- The goal involves the **Smith normal form** of an integer matrix (invariant factors, unimodular equivalence) or the
  **Jordan form** or diagonalization of a rational matrix with rational eigenvalues.
- `smith_certificate(A)` returns `D, U, V` with facts `hsmith : U * A * V = D`, `hU : U * U⁻¹ = 1`, `hV : V * V⁻¹ = 1`
  (integer inverses, so `U` and `V` are unimodular). `jordan_certificate(A)` returns `J, P` with
  `hjordan : A * P = P * J` and `hP : P * P⁻¹ = 1`. The kernel checks every product.

## Template

Copy it to the project's `.veriphy/certificates/matrix_normal_form.sage` (or a more specific name), adapt the lines marked `EDIT`,
keep the header, and run it with `sage_run file "<name>.sage"`.

```sage
# name: matrix_normal_form
# technique: Smith and Jordan normal forms with explicit transformation matrices and inverses
# goal: a statement about the Smith form, Jordan form or diagonalization of an explicit matrix
# description: Sage computes the form and the transformations; the kernel checks U A V = D or A P = P J and the inverses.
MATRIX = None  # EDIT: the matrix (Sage), integer for a Smith form, rational with rational eigenvalues for a Jordan form
FORM = 'jordan'  # EDIT: 'smith' or 'jordan' (a diagonalizable matrix gets a diagonal Jordan form)
CLOSE = 'trivial'  # EDIT: the tactic closing the goal from the facts (hsmith, hU, hV or hjordan, hP)
assert MATRIX is not None, 'fill in MATRIX (and FORM) in a copy'
if FORM == 'smith':
    d, u, v, facts = smith_certificate(MATRIX)
    print('D =', d.diagonal())
else:
    j, p, facts = jordan_certificate(MATRIX)
    print('J =', j)
proof = steps(facts, tactic(CLOSE))
```

## Worked examples

```lean
-- with MATRIX = matrix(ZZ, [[2, 4, 4], [-6, 6, 12], [10, -4, -16]]) and FORM = 'smith'
example : True := by
  sage_run file "smith_example.sage"
```

`VeriphyTest/SageRun.lean` also checks a Jordan form with a nontrivial block.

## Failure modes

- **"fill in MATRIX":** copy the template and fill in the matrix.
- **"the eigenvalues are not all rational":** work over a number field (`quadratic_context`, `field_matrix_identity`)
  for the identity `A * P = P * J`.
- **A rectangular matrix:** the kernel checkers are for square matrices; pad, or prove the product identities
  entrywise.
