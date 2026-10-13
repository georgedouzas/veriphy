# certificates/translation-coverage Specification

## Purpose
Measures how much of a real corpus of statements the symbolic translation covers. It reports the opaque function heads that matter most, so new core or project entries follow data rather than guesses.

## Requirements

### Requirement: Coverage command
A Sage-free Lean command SHALL take a list of module prefixes and walk the theorem statements declared in matching modules. For each statement it opens the binders and translates every relation (`=`, `≠`, `≤`, `<`, `≥`, `>`) in the hypotheses and the conclusion. Statements with no relation SHALL be counted separately and excluded from the shares.

#### Scenario: Statement without a relation
- **WHEN** a statement is `Continuous f`
- **THEN** it is counted among statements with no relation, and not in the shares

### Requirement: Atom classification
The coverage command SHALL classify each atom of a translation as a local variable or numeral, an uninterpreted local function application (head is a bound variable), or an opaque term with a global head constant. A statement is fully covered when every atom is of the first kind.

#### Scenario: Statement fully covered
- **WHEN** a statement is `∀ x : ℝ, 0 < x → Real.log (x ^ 2) = 2 * Real.log x`
- **THEN** it counts as fully covered, since every atom is a local variable

#### Scenario: Statement with an opaque head
- **WHEN** a statement's relation contains `Real.Gamma x`
- **THEN** the statement counts as not covered, and `Real.Gamma` is counted once in the opaque heads

### Requirement: Coverage report
The command SHALL write a JSON report and print a summary with:
- the number of statements with a relation;
- the share fully covered;
- the share covered up to uninterpreted local functions;
- the 30 most frequent opaque head constants, with their counts and one example statement name each.

#### Scenario: Report for a corpus
- **WHEN** the command runs over the `Archive` modules
- **THEN** the report lists the three numbers and the ranked heads, and the JSON holds the same data

### Requirement: Measured corpora
A runner, separate from the library build, SHALL measure:
- Physlib, at a pinned revision compatible with Veriphy's mathlib;
- Mathlib's `Archive`;
- mathlib's `Mathlib.Analysis.ODE`, `Mathlib.Algebra.Lie` and `Mathlib.Geometry.Manifold`.

Results SHALL be reported per corpus and per active namespace.

#### Scenario: Per-corpus report
- **WHEN** the runner finishes
- **THEN** there is one report per corpus, each listing the active namespaces

### Requirement: Recorded results
The baseline before this change's core entries and the result after them SHALL be recorded in `docs/development/coverage.md`, with the corpus revisions, the date and the top opaque heads. Each listed head SHALL be marked as one of: added to the core, added to a library pack, a candidate for a project entry, or out of scope (with the reason).

#### Scenario: Before and after
- **WHEN** the core categories of this change are implemented
- **THEN** `docs/development/coverage.md` shows the baseline and post-change shares for every corpus, and the post-change fully-covered share is at least the baseline's for each
