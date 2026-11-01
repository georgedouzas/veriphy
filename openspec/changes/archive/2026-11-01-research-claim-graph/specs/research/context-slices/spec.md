# Spec Delta

## Purpose

Gives the proving agent, for one claim, exactly the statements, conventions and definitions the claim rests on, with a
check that the slice keeps every consequence about the claim that the full graph has.

## ADDED Requirements

### Requirement: Slice of a claim
The graph CLI SHALL compute the slice of a claim: the claim's own assertions and every asserted triple that a
derivation of a consequence about the claim cites, directly or through earlier derivation lines.

#### Scenario: Slicing a theorem
- **WHEN** a user asks for the slice of `thm-9.1`, which uses `lemma-5.2` and assumes `mostly-minus` through it
- **THEN** the slice holds the assertions of `thm-9.1` and `lemma-5.2`, the `assumes` triple, and the convention's
  own assertions, and holds nothing about unrelated claims

### Requirement: A slice keeps its consequences
For every slice, Veriphy SHALL reason over the slice alone, have the run checked by `oo-horn`, and compare the
consequences about the claim with those of the full graph. A slice that loses a consequence SHALL be reported with the
lost triples and SHALL NOT be offered to the agent.

#### Scenario: A complete slice
- **WHEN** the slice of `thm-9.1` derives every `assumes`, cap and clash about `thm-9.1` that the full graph derives
- **THEN** the report says the slice keeps all consequences about the claim, with the checker's verdict for both runs

#### Scenario: A lost consequence
- **WHEN** a slice misses a premise and loses `thm-9.1 assumes mostly-minus`
- **THEN** the report lists that triple as lost, and the slice is not offered

### Requirement: Slice as agent context
The graph CLI SHALL render a slice as Markdown for the agent: the claim's statement, the statements of what it uses,
each convention with its statement and the aspect it fixes, the Lean names of formalized nodes, and the effective
levels.

#### Scenario: Context before formalizing
- **WHEN** an agent asks for the context of `eq-7.3` before formalizing it
- **THEN** it receives the Markdown slice, which names the conventions `eq-7.3` assumes and the Lean definitions that
  realize them
