# research/graph-checks Specification

## Purpose
Checks a research graph for missing information and for clashing conventions, within a source and across sources,
keeping a measurement apart from a checked conclusion.

## Requirements

### Requirement: Shapes for claims
Veriphy SHALL ship SHACL shapes for the vocabulary: a claim has a source and a statement, a convention names what it
is a convention for, a `formalizedBy` link points to an exported Lean claim, and a `realizedBy` link points to an
exported Lean definition. The graph CLI SHALL validate the graph against them.

#### Scenario: A claim without a statement
- **WHEN** `chapter3.agent.ttl` holds the claim `eq-3.4` with no statement
- **THEN** validation reports `eq-3.4`, the shape it breaks and the file it is in

#### Scenario: A broken Lean link
- **WHEN** `eq-3.12` is formalized by a Lean name that the export does not hold
- **THEN** validation reports the link and the missing name

### Requirement: Validation is a measurement
A SHACL report SHALL be labelled as a measurement by the validator, and SHALL NOT carry a checker verdict word.

#### Scenario: A clean validation
- **WHEN** the graph conforms to every shape
- **THEN** the report says the graph conforms according to the SHACL validator, and does not call the graph checked

### Requirement: Exclusive conventions
Conventions for the same aspect, such as the metric signature or the normalization of the Killing form, SHALL be
declared to exclude each other with `excludes`, which is symmetric. The graph CLI SHALL generate the `excludes` triples
for conventions that share a `conventionFor` value, with provenance `human` only after a person confirms them.

#### Scenario: Two metric signatures
- **WHEN** `mostly-minus` and `mostly-plus` both have `conventionFor metric-signature`
- **THEN** the CLI proposes `mostly-minus excludes mostly-plus` for confirmation

### Requirement: Certified clashes
The graph CLI SHALL report a clash for every claim or concept with two checked `assumes` conclusions whose conventions
exclude each other by an asserted `excludes` triple, including assumptions inherited through `uses` and `owl:sameAs`
across sources. A clash SHALL cite both derivations, the `excludes` triple and the checker's verdict.

#### Scenario: A clash across papers
- **WHEN** `thm-9.1` uses `lemma-5.2`, which assumes `killing-normalization-half`, and uses claim `thm-2` of
  `arXiv:0808.3236`, which assumes `killing-normalization-one`, and the two exclude each other
- **THEN** the check reports a clash on `thm-9.1`, cites both chains, and shows the verdict `oo-horn` printed

#### Scenario: No clash
- **WHEN** no node assumes two exclusive conventions
- **THEN** the check reports no clash, and the report says that the absence of a clash is the reasoner's result and not
  a checked conclusion
