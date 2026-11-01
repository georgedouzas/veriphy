# Triage

## When to use

- Step 3 of `prompts/research.md`, after extraction and validation.
- Every claim of the source gets exactly one group, recorded in the agent file as `vp:triage "<group>"`.

## Groups

| Group | When | Next |
|---|---|---|
| `suspect` | the numerical check fails at a point that satisfies the hypotheses | record the point in the report, do not prove |
| `recipe` | the claim, once formalized, has a goal shape in the recipe index of `prompts/prove.md` | prove it with the recipe |
| `test` | no recipe applies and the claim quantifies over a dimension, a space or a function | `sage_test` it, level `kernel-test` or `oracle-test` |
| `formalize` | the claim needs definitions or theory the workspace does not have yet | formalize first, report what is missing |

## Order

1. Run the numerical check of `prompts/prove.md` step 1 on every claim that has a computable form: render it in Sage
   and evaluate it at random points that satisfy its hypotheses, under the conventions it assumes (read them with
   `sage -python -m veriphy.graph slice <source> <label>`). A counterexample puts the claim in `suspect`, with the
   point. A convention clash is a common cause: check `sage -python -m veriphy.graph clashes` before blaming the
   claim.
2. Sort the rest into `recipe`, `test` and `formalize` by the table above. When in doubt between `recipe` and `test`,
   choose `recipe`: the fallback applies only after recipe selection failed.

## Template

```turtle
@prefix vp: <urn:veriphy:vocabulary#> .
@prefix : <urn:veriphy:source:chapter9#> .

:eq-9.2 vp:triage "recipe" .
:thm-9.1 vp:triage "formalize" .
:eq-9.7 vp:triage "suspect" .
```
