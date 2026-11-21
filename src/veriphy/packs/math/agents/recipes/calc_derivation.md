# Calc derivation

## When to use

- A long manipulation: substitutions, expansions, normal forms, as in physics derivations.
- Sage computes the intermediate expressions. Each `calc` step closes with its own tactic (`ring`, `field_simp`, `norm_num`), so a failure points at one step.

## Template

Copy it to the project's `.veriphy/certificates/calc_derivation.sage` (or a more specific name), adapt the lines marked `EDIT`, keep the header, and run it with `sage_run file "<name>.sage"`.

```sage
# name: calc_derivation
# technique: calc derivation (each step checked on its own)
# goal: lhs = rhs (or ≤ / <) reached through intermediate expressions Sage computes
# description: Chain intermediate forms from Sage; each calc step closes by its own tactic, so a failure names the step.
start = lhs.text  # EDIT: the goal's left side, or a rewritten form of it
middle = expand(SR(str(lhs.poly)))  # EDIT: any intermediate Sage computes (expanded, factored, substituted, ...)
chain = [
    ('=', R(str(middle)), tactic('ring')),  # EDIT: one step per intermediate, each with its own tactic
    ('=', term(rhs.text), tactic('ring')),
]
proof = calc_chain(term(start), chain, problem)
```

## Worked example

```lean
example (x : ℚ) : (x + 1) ^ 2 - 1 = x * (x + 2) := by
  sage_run file "calc_derivation.sage"
```

## Failure modes

- **One step fails:** that intermediate is wrong, or needs a hypothesis. Split the step in two, or justify it with `linear_combination h` instead of `ring`.
- **Denominators:** justify the step with `field_simp` then `ring`, and keep the nonzero facts in the context.
