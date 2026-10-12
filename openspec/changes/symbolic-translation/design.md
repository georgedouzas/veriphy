# Design

## Context

- **Translation today.** `Veriphy/Translate.lean`'s `exprToSage` handles `+ - * ^ₙ`, negation, numerals and division by numerals. Every other subterm becomes an atom. `withLenientProblem` adds Lean text for everything, and polynomial forms where they exist.
- **Emitters today.** Python emitters render rationals and polynomials of the problem ring.
- **LeanSage.** LeanSage (MIT, `~/Projects/Public/LeanSage`) translates through a `MathAST`:
  - `ExprToAST.lean` (648 lines) covers `Real`/`Complex` functions, constants, casts, `Fin` arithmetic, lists and sets, intervals, `Ideal.span`, the `Polynomial` API, `deriv`/`iteratedDeriv`, integrals, and matrix literals and operations;
  - `ASTToSage.lean` and `ASTToLean.lean` render the AST both ways;
  - its `abs` maps to `Int.natAbs` regardless of type, a bug Veriphy must not copy.

## Goals / Non-Goals

**Goals:**
- Scripts see the full structure of goals and hypotheses as Sage objects.
- Scripts emit Lean that uses that structure.
- Lean can check what scripts emit: every side condition a check needs is visible, and named when a hypothesis provides it.

**Non-Goals:**
- Translating derivatives, integrals and limits. Scripts may compute them in Sage, but the proofs need analysis lemmas, which are recipe material and not translation.
- Sets, intervals, `Ideal.span` and `Fin` arithmetic, unless a recipe needs them. They can be added later in the same way.
- Trusting any translation. A mistranslation makes the emitted proof fail, and never proves something else.

## Decisions

### D1. A typed intermediate representation in Lean, Sage text on the wire

A small `SymExpr` inductive is added in Lean, modelled on LeanSage's `MathAST` but limited to the coverage list:
- numbers;
- typed atoms;
- the field operations and powers;
- applications of the function table;
- constants;
- range sums and products;
- matrices;
- polynomial operations.

It renders to Sage syntax for the wire, so the daemon parses it with `SR(...)`, or `matrix(SR, …)` for matrices. The polynomial translator stays as it is, and the symbolic form is additional. *Alternative:* send `MathAST` JSON and rebuild it in Python. Rejected: Sage parses its own syntax robustly, and the tables are simpler with text.

### D2. Port LeanSage's tables, with attribution

The Lean-constant-to-Sage-function and Sage-function-to-Lean tables are ported from LeanSage's `ExprToAST.lean` and `ASTToLean.lean`, credited in a header comment and in the docs. The port corrects `abs` to dispatch on the type. Porting means copying table entries, not taking a dependency, because LeanSage pins its own Lean and mathlib versions.

### D3. Domain conditions are collected during translation

While building `SymExpr`, the translator records a `Condition` for each non-numeral denominator (`≠ 0`), `sqrt` argument (`0 ≤`) and `log` argument (`0 <`). After translation it looks each one up among the hypotheses, using the same relation normalization as constraints, up to reducible defeq. A match is recorded by name; anything else is recorded as undischarged.

### D4. Python binding

- `Hyp` gains `expr` (an SR expression or `None`).
- `Problem` gains `atom_types` and `domain` (a list of `Condition(text, expr, rel, discharged_by)`).
- Atom generators also exist as SR variables, with the same names, for symbolic work.
- The polynomial ring stays for polynomial-only scripts.

### D5. Symbolic emitters

`toolkit._symbolic_emit.symbolic(expr, problem)` walks SR expressions (`operator()` and `operands()`) and emits through the function table, rejecting unmapped operators. Its companions are:
- `matrix_term(M, problem)`;
- `field_simp_clearing(problem)`, which passes discharged denominators;
- `lemma_rewrite(lemma, …)`.

### D6. Recipes and tests

- **New recipes:** `rational_inequality` (clear denominators with `field_simp`, then `sos`/`hint_search` on the numerator), `transcendental_rewrite` (lemma chains) and `matrix_from_goal`.
- **Round-trip tests:** a Lean test file translates one term per covered construct and renders it back through the daemon, with `example : orig = rendered := by norm_num` or `ring_nf`.

## Risks / Trade-offs

- **[Risk]** Function-name collisions or branch-cut differences (complex `log`). → The table dispatches on the Lean type. Complex branch cuts are left as text-only, outside the coverage list, until a recipe needs them.
- **[Risk]** Sage's simplification changes the form of an expression the script then renders, for example `sqrt(x^2)` becoming `abs(x)`. → Emitted text is checked by Lean anyway. Recipes advise rendering from the script's own constructed expressions, not from simplified output.
- **[Trade-off]** The `SymExpr` intermediate representation duplicates part of `exprToSage`. Polynomial translation stays separate because it feeds the exact polynomial ring, which most recipes use.

## Migration Plan

This applies after `sage-building-blocks` is archived. All changes are additive: existing scripts keep working, and the new fields are optional.
