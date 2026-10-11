# certificates/problem-extraction Specification

## Purpose
Turns a Lean goal and its local context into one normalized constraint problem that every certificate tactic and the generic `sage_certify` tactic share, so parsing and atom bookkeeping are written once.

## Requirements

### Requirement: Shared atom table
All expressions extracted for one tactic invocation SHALL be translated against a single atom table, so a subterm that appears in both the goal and a hypothesis (up to reducible defeq) maps to the same Sage indeterminate.

#### Scenario: Atom shared between goal and hypothesis
- **WHEN** the goal is `f a ^ 2 = 1` and a hypothesis is `h : f a = 1`
- **THEN** both translations use the same indeterminate for `f a`, and the atom table contains it exactly once

#### Scenario: Atom table order is stable
- **WHEN** the same goal and context are extracted twice
- **THEN** the atom table lists the same atoms in the same order both times

### Requirement: Relation normalization
Each extracted constraint SHALL be one of `p = 0`, `p ≤ 0`, `p < 0` or `p ≠ 0`, where `p` is the difference of the two sides. `a ≥ b` and `a > b` SHALL be flipped to `b - a ≤ 0` and `b - a < 0`, and `¬ (a = b)` SHALL be read as `≠`.

#### Scenario: Greater-or-equal hypothesis
- **WHEN** the context contains `h : x ≥ 2`
- **THEN** the extracted constraint is `2 - x ≤ 0`, with source hypothesis `h`

#### Scenario: Negated equality
- **WHEN** a conjunct is `¬ (v = 0)`
- **THEN** it is extracted as `v ≠ 0`

### Requirement: Hypothesis collection
The extractor SHALL collect the context hypotheses whose type is a supported relation over the problem's carrier type, recording each one's user name. Hypotheses that fail to translate SHALL be skipped without changing the atom table.

#### Scenario: Untranslatable hypothesis is skipped cleanly
- **WHEN** the context contains `h1 : x + y = 1` and `h2 : Real.sin x = 0`, and the carrier is `ℚ`-polynomial-translatable only for `h1`
- **THEN** only `h1` is collected, and no atom from `h2` is in the atom table

#### Scenario: Different carrier type is ignored
- **WHEN** the goal is over `ℚ` and the context contains `n : ℕ` with `hn : n ≤ 3`
- **THEN** `hn` is not collected

### Requirement: Inaccessible hypotheses are excluded
Hypotheses whose names cannot be written in source (inaccessible or macro-scoped names, implementation details) SHALL never be collected. This keeps every extracted constraint referable from a printed proof.

#### Scenario: Shadowed hypothesis
- **WHEN** the context contains an inaccessible `h✝ : x = 1` and an accessible `h : y = 2`
- **THEN** only `h` is collected

### Requirement: Goal classification
The extractor SHALL classify the goal as one of: a relation (`=`, `≤`, `<`, `≠` and their flips), `False`, an existential over one or more binders, or unsupported. An unsupported goal SHALL raise an error that names the tactic and shows the goal.

#### Scenario: Unsupported goal shape
- **WHEN** `sage_lincomb` runs on a goal `x ∣ y`
- **THEN** it fails with an error naming `sage_lincomb` and showing the goal

### Requirement: Existential peeling and conjunction splitting
For an existential goal, the extractor SHALL bind every leading `∃` variable as a local, register them as the first atoms in binder order, and split the body's conjunctions into individual constraints. Any atom other than a binder SHALL be reported as an error.

#### Scenario: Two binders and three conjuncts
- **WHEN** the goal is `∃ x y : ℚ, x + y = 1 ∧ 0 < x ∧ x < y`
- **THEN** the problem has binders `[x, y]` as atoms 0 and 1, and three constraints: one `=` and two `<`

#### Scenario: Free parameter in an existential body
- **WHEN** the goal is `∃ x : ℚ, x = a` with `a` a context variable
- **THEN** extraction fails with an error stating that the body has free subterms other than the bound variables

### Requirement: Sage encoding of a problem
A problem SHALL serialize to the daemon as: variable names, each constraint's polynomial and relation tag, the source hypothesis names, the goal constraint (if any), the binder count, and a pretty-printed Lean form of each atom.

#### Scenario: Serialization round trip
- **WHEN** a problem with two hypotheses and a `≤` goal is serialized
- **THEN** the JSON lists two hypothesis entries with names and relations `eq`/`le`/`lt`/`ne`, one goal entry, and one name and one Lean rendering per atom
