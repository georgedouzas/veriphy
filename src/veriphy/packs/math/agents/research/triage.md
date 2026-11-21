# Triage

## When to use

- Step 3 of `research.md`, after extraction and validation.
- Every claim of the source gets exactly one group, recorded in the agent file as `vp:triage "<group>"`.

## Groups

| Group | When | Next |
|---|---|---|
| `suspect` | the meaning check finds a counterexample: values that satisfy the hypotheses and not the claim | record the values and the record's path in the report, do not prove |
| `recipe` | the claim, once formalized, has a goal shape in the recipe index of `prove.md` | prove it with the recipe |
| `test` | no recipe applies and the claim quantifies over a dimension, a space or a function | `#veriphy test` it, level `kernel-test` or `oracle-test` |
| `formalize` | the claim needs definitions or theory the workspace does not have yet | formalize first, report what is missing |

## Order

1. Run the meaning check of `prove.md` step 1 on every claim that has a computable form, once it is stated in Lean
   under the conventions it assumes (read them with `sage -python -m veriphy layers claims slice <source> <label>`):
   `veriphy layers step meaning <file> <declaration> --informal "<the claim's text>"`. A `counterexample` puts the
   claim in `suspect`, with the values and the path of the record. A convention clash is a common cause: check
   `sage -python -m veriphy layers claims clashes` before blaming the claim. An `undecided` claim is triaged as usual, and the
   report says it was not tested.
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
