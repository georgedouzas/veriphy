# Spec Delta

## Purpose

Lets an agent carry a research draft through Veriphy: extract its claims into the graph, triage them, prove them with
their slices, and report the verification of every claim in an appendix the paper can include.

## ADDED Requirements

### Requirement: Research skill
The plugin SHALL ship a `research` skill that leads the agent through extraction, triage, proving, export and
reporting for one source, using the graph CLI at each step, and SHALL work with the graph extra installed and Sage
absent for every step except proving.

#### Scenario: Running the skill on a chapter
- **WHEN** a user asks the agent to verify `chapter9.tex` with the research skill
- **THEN** the agent extracts the claims, triages them, proves what it can, exports the Lean claims, and writes the
  appendix for `chapter9`

### Requirement: Claim extraction from a draft
The skill SHALL extract claims, conventions, concepts and dependencies from a LaTeX or Markdown draft into
`<source>.agent.ttl`, with each claim's statement and its location in the draft, and SHALL validate the result against
the shapes before it continues.

#### Scenario: Extracting a LaTeX chapter
- **WHEN** the agent extracts `chapter9.tex`
- **THEN** `chapter9.agent.ttl` holds one claim per numbered equation, lemma and theorem the chapter states, each with
  its label and line, and validation passes

### Requirement: Triage
The skill SHALL sort the claims of a source into four groups: a recipe applies, `sage_test` applies, formalization is
needed first, and statement suspect after a numerical check. It SHALL record the group of each claim in the graph.

#### Scenario: A suspect claim
- **WHEN** the numerical check of `eq-9.7` fails at a sample point
- **THEN** `eq-9.7` is recorded as statement suspect with the failing point, and the agent does not try to prove it

### Requirement: Proving with a slice
Before the `prove` workflow formalizes a claim that is in the graph, it SHALL load the claim's slice and state the
claim under the conventions the slice names. After a proof, the skill SHALL link the claim to its Lean name and run
the export again.

#### Scenario: Formalizing under the right convention
- **WHEN** the agent formalizes `eq-7.3`, whose slice names `mostly-minus` realized by `KK.minkowski`
- **THEN** the Lean statement of `eq-7.3` uses `KK.minkowski`, and after the proof `eq-7.3` is formalized by the new
  theorem in the graph

### Requirement: Verification appendix
The graph CLI SHALL write, for a source, a verification appendix in Markdown and in LaTeX: every claim with its label,
own level, effective level, capping claim, Lean name and clashes, the provenance counts of the assertions, the
checker's verdict for the run, and the commands that recheck it.

#### Scenario: Appendix for a chapter
- **WHEN** a user asks for the appendix of `chapter9` in LaTeX
- **THEN** the CLI writes a `.tex` file with one table row per claim and a paragraph that names the run, the verdict,
  and the recheck command

#### Scenario: Appendix without a checker
- **WHEN** the run behind the appendix is unchecked
- **THEN** the appendix states that its effective levels are unchecked, in its first paragraph and in its table header
