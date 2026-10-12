# Proposal

## Why

Scripts can only see what Veriphy translates, and today that is polynomial arithmetic over atoms. Everything else is opaque:
- `x / y` and `Real.sin x` become atoms with no structure;
- `x ^ n` with a symbolic exponent, matrices, `Polynomial` objects and casts arrive as text only.

Goals in physics are full of rational functions, roots, exponentials, trigonometry, complex numbers and explicit matrices. A script cannot use the structure of `x / (x^2 + 1) ≤ 1/2` or `Real.exp a * Real.exp b = Real.exp (a + b)`.

The emitters have the mirror-image limit: they render rationals and polynomials, but not rational functions or symbolic expressions.

[LeanSage](https://github.com/oOo0oOo/LeanSage) (MIT) solved the translation breadth, but it trusts the result and closes goals with `sorry`. Veriphy keeps the kernel as the only judge. It needs the breadth together with what checking requires: the side conditions (`y ≠ 0`, `0 ≤ u` under `√u`, `0 < u` under `log u`) that Lean's `field_simp`, `positivity` and lemma rewrites need.

## What Changes

- **Symbolic forms for every constraint.** Next to the existing polynomial form, each hypothesis and goal gets a Sage symbolic-ring expression, `expr`, whenever it translates. That covers:
  - rational functions;
  - `Real`/`Complex` `sqrt`, `exp`, `log`, `sin`, `cos`, `tan`, and `π`, `e`, `I`;
  - `|·|`, `%`, powers with symbolic exponents;
  - ℕ/ℤ/ℚ/ℝ/ℂ literals and casts;
  - `Finset.range` sums and products;
  - explicit matrices and their `det`, `trace`, `transpose`, `inv`;
  - `Polynomial` expressions (`X`, `C`, `eval`, `coeff`, `degree`).

  Untranslatable subterms stay atoms, as today.
- **Typed atoms.** Each atom carries its Lean type (ℕ, ℤ, ℚ, ℝ, ℂ, or a matrix type), and scripts see the facts that follow from the type, such as `0 ≤ ↑n` for a natural cast.
- **Domain conditions.** Extraction reports the conditions each expression needs: denominators nonzero, arguments of `sqrt` nonnegative, arguments of `log` positive. For each one it says whether a hypothesis already discharges it, by name.
- **Symbolic emitters.** Emitters render Sage symbolic expressions, rational functions and matrices back to Lean text, with an explicit function table (`sqrt` → `Real.sqrt`, `abs` → `|·|`, …). They build `field_simp`/`positivity` calls carrying the domain-condition facts.
- **Recipes:** new recipes for rational-function inequalities (clear denominators, then `sos`/`hint_search`), transcendental rewrites (lemma chains such as `Real.exp_add`), and matrix identities read from the goal instead of retyped.
- **Attribution:** the translation tables port LeanSage's (MIT), credited in the source and the docs.

## Capabilities

### New Capabilities
- `certificates/symbolic-translation`: the symbolic forms, typed atoms and domain conditions that extraction gives scripts.
- `certificates/symbolic-emitters`: rendering symbolic expressions, rational functions and matrices back to Lean, and building denominator- and domain-aware tactic calls.

### Modified Capabilities
<!-- none in the main specs: this extends capabilities introduced by the in-flight `sage-building-blocks` change (script-tactic, lean-emitters, procedures); it is applied after that change is archived -->

## Impact

- **Lean:** `Veriphy/Translate.lean` gains a symbolic translator beside `exprToSage`; `Veriphy/Kit/Problem.lean` serializes `expr`, atom types and domain conditions.
- **Python:** `veriphy.toolkit` binds symbolic forms (`Hyp.expr`, `Problem.domain`) and adds symbolic emitters.
- **Recipes and tests:** new recipes and templates, plus examples in `VeriphyTest/SageRun.lean`, and translation round-trip tests in the style of LeanSage's `Test/Roundtrip.lean`.
- **Dependency:** applied after `sage-building-blocks` is archived.
