# Claim extraction

## When to use

- Step 1 of `prompts/research.md`: a source enters the research claim graph.
- The source is a LaTeX or Markdown draft. The output is `.veriphy/graph/sources/<source>.agent.ttl`, where
  `<source>` is the file stem (`chapter9`), an arXiv identifier (`arXiv:0808.3236`) or a DOI.

## What to extract

- **Claims.** One `vp:Claim` per numbered equation, lemma, proposition, theorem and corollary the source states, and
  per unnumbered statement that a later claim relies on. Label it as the source does (`eq-3.12`, `lemma-5.2`,
  `thm-9.1`). Give it `vp:statedIn`, a `vp:statement` with the statement's text (LaTeX kept as written), and a
  `vp:location` with the file and line.
- **Conventions.** One `vp:Convention` per choice a statement depends on: metric signature, normalization of
  generators or forms, sign of the curvature, units, index placement, ordering of a basis. Give it `vp:statement`
  and `vp:conventionFor` with the aspect it fixes (`metric-signature`, `killing-normalization`). Two conventions of
  the same aspect have the same `vp:conventionFor` value.
- **Concepts.** One `vp:Concept` per notion the source defines or uses in several claims, with `vp:statement`. A
  claim that defines it has `vp:defines`.
- **Dependencies.** `vp:uses` from a claim to each claim, concept or Lean definition its derivation relies on. A
  claim of an earlier paper is a node of that paper's source: `<urn:veriphy:source:arXiv:0808.3236#thm-2>`.
- **Assumptions.** `vp:assumes` from a claim or concept to each convention it is stated under. State it where the
  source fixes it. Reasoning carries it to every claim that uses the node.
- **Lean links.** `vp:realizedBy <urn:veriphy:lean:<name>>` from a convention to a Lean definition that realizes it,
  and `vp:formalizedBy` from a claim to its Lean claim, only when those declarations exist.

## Rules

- Extract what the source says, not what it should say. A missing dependency is a finding for the report, not a
  triple to invent.
- Never write blank nodes. Every node has an IRI.
- Never assert `vp:hasLevel` for a prose claim. Levels come from the Lean export.

## Template

```turtle
@prefix vp: <urn:veriphy:vocabulary#> .
@prefix : <urn:veriphy:source:chapter9#> .

:mostly-minus a vp:Convention ; vp:conventionFor "metric-signature" ; vp:statement "η = diag(1, -1, -1, -1)" .
:killing-form a vp:Concept ; vp:statement "The Killing form of the coset space G/H." .
:eq-9.2 a vp:Claim ; vp:statedIn :chapter9 ; vp:location "chapter9.tex:212" ;
    vp:statement "B(X, Y) = -\\frac{3}{2} \\delta_{XY}" ; vp:defines :killing-form ; vp:assumes :mostly-minus .
:thm-9.1 a vp:Claim ; vp:statedIn :chapter9 ; vp:location "chapter9.tex:240" ;
    vp:statement "The vacuum is stable." ; vp:uses :eq-9.2, <urn:veriphy:source:arXiv:0808.3236#thm-2> .
```

Then run `sage -python -m veriphy.graph validate`.
