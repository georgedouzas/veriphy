# Spec Delta

## Purpose

Records the structure of a research project as an RDF graph: its claims, the conventions and concepts they use, the
sources they come from, and how they depend on each other, with the origin of every assertion.

## ADDED Requirements

### Requirement: Veriphy vocabulary
Veriphy SHALL ship one RDF vocabulary for research graphs, in Turtle, with the classes `Claim`, `Convention`,
`Concept` and `Source`, and the properties `uses`, `assumes`, `defines`, `statedIn`, `statement`, `leanName`,
`formalizedBy`, `realizedBy`, `hasLevel`, `conventionFor` and `excludes`. The four levels SHALL be individuals of the
vocabulary, with their order stated as triples.

#### Scenario: Reading the vocabulary
- **WHEN** a user asks the graph API for the vocabulary
- **THEN** it returns the Turtle file, and the file states `none` below `oracle-test` below `kernel-test` below
  `certificate`

#### Scenario: A graph with an unknown property
- **WHEN** a source file uses a property in the Veriphy namespace that the vocabulary does not declare
- **THEN** loading the graph fails and names the property and the file

### Requirement: Graph files
A project's graph SHALL be the union of the Turtle files under `.veriphy/graph/sources/` and the Lean export under
`.veriphy/graph/lean/`. A file under `sources/` SHALL be named `<source>.<provenance>.ttl`, SHALL hold triples about
one source (a paper, a chapter or a set of notes) with one provenance, and SHALL be valid Turtle.

#### Scenario: Loading a project graph
- **WHEN** `.veriphy/graph/sources/` holds `chapter3.agent.ttl`, `chapter3.human.ttl` and `0808.3236.human.ttl`, and
  `.veriphy/graph/lean/` holds an export
- **THEN** the loaded graph holds the triples of all four files, and its report names each file with its triple count

#### Scenario: A file without a provenance
- **WHEN** `.veriphy/graph/sources/` holds `chapter3.ttl`
- **THEN** loading fails and asks for the name `chapter3.<provenance>.ttl` with `agent` or `human`

#### Scenario: A syntax error
- **WHEN** `chapter3.agent.ttl` has a Turtle syntax error
- **THEN** loading fails, names the file, the line and the parser's message, and no reasoning runs

### Requirement: Node identity
Every claim, convention and concept SHALL have an IRI under its source's namespace, built from the source identifier
and a local label such as `eq-3.12` or `killing-normalization`. A claim exported from Lean SHALL have an IRI built
from its Lean name. The same label in two sources SHALL name two nodes.

#### Scenario: Two sources with the same label
- **WHEN** `chapter3.agent.ttl` and `chapter5.agent.ttl` both define a claim labelled `lemma-1`
- **THEN** the graph holds two distinct claims

#### Scenario: A Lean claim
- **WHEN** the export contains the theorem `KK.Coset.killing_form_value`
- **THEN** its node IRI is derived from that name, and the same name always gives the same IRI

### Requirement: Provenance of assertions
Every asserted triple SHALL carry its provenance: `lean` for triples the Lean export wrote, `agent` for triples an
agent extracted, `human` for triples a person wrote or confirmed, and `veriphy` for the vocabulary axioms Veriphy
generates. Reports that state a conclusion SHALL count the provenance of the assertions it rests on.

#### Scenario: Agent extraction
- **WHEN** an agent extracts the claims of a draft
- **THEN** it writes them to `chapter3.agent.ttl`, and each triple it wrote has provenance `agent`

#### Scenario: Confirming an assertion
- **WHEN** a person confirms an extracted `assumes` triple through the graph CLI
- **THEN** the triple moves from `chapter3.agent.ttl` to `chapter3.human.ttl`, and no other triple changes

### Requirement: Links between sources
A claim SHALL be able to use a claim of another source, and a concept of one source SHALL be declared the same as a
concept of another with `owl:sameAs`. An external paper SHALL be a source identified by its arXiv identifier or DOI.

#### Scenario: Building on an earlier paper
- **WHEN** `chapter3.agent.ttl` states that `eq-3.12` uses claim `thm-2` of the source `arXiv:0808.3236`
- **THEN** reasoning over the graph follows that dependency into the other source

#### Scenario: One concept, two papers
- **WHEN** the Killing form of `chapter3` is declared `owl:sameAs` the Killing form of `arXiv:0808.3236`
- **THEN** conventions stated for either node apply to both in reasoning
