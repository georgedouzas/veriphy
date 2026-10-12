# Spec Delta

## Purpose

Lets a project extend the symbolic translation with functions and rewrite lemmas Veriphy does not cover. Entries live in the project, are checked by a round trip, and take effect with no Veriphy release.

## ADDED Requirements

### Requirement: Entries live in the project
Translation entries SHALL be JSON files in the project's `translations/` directory, resolved against the workspace root as certificate scripts are. Each file SHALL be validated against a declared schema. An invalid file SHALL be reported naming the file and the field, and SHALL NOT be loaded.

#### Scenario: Invalid entry
- **WHEN** `translations/cosh.json` lacks its Sage name
- **THEN** extraction reports `translations/cosh.json: missing field 'sage'` and the other entries still load

### Requirement: Entry format
A function entry SHALL give:
- the Lean constant and its arity;
- the Sage name;
- the argument and result types it applies to;
- its domain conditions, by argument;
- a round-trip example, as a Lean term over named variables.

A rewrite entry SHALL give the lemma name, the functions it applies to, the rewrite direction, its side conditions and a worked example goal. One file MAY hold several entries.

#### Scenario: Function entry with a condition
- **WHEN** an entry maps `Real.arcosh` to Sage `arccosh` with the condition `1 ≤ x` on its argument
- **THEN** a goal containing `Real.arcosh y` gets the symbolic form `arccosh(y)` and the domain condition `1 ≤ y`

### Requirement: One source for both directions
The same entries SHALL drive the Lean-to-Sage translation and the Sage-to-Lean rendering. The extracted problem SHALL carry the project's entries, so the daemon renders with exactly the table the translation used.

#### Scenario: Rendering with a project entry
- **WHEN** a project entry maps `Real.cosh` to `cosh` and a script renders a Sage result containing `cosh`
- **THEN** the rendered text uses `Real.cosh`

### Requirement: No silent override
A project entry SHALL NOT redefine a core entry or another project entry. A conflict SHALL be reported naming both entries, and the conflicting project entry SHALL NOT be loaded.

#### Scenario: Conflict with the core
- **WHEN** a project entry maps `Real.exp` to a different Sage name
- **THEN** extraction reports the conflict with the core entry for `Real.exp`, and the core entry stays in force

### Requirement: Round-trip check
A Lean command SHALL check every project entry. For each entry it translates the round-trip example, renders it back through the daemon, and proves the rendering equal to the original. It reports each entry as passed or failed, with Lean's error for a failure. For each rewrite entry, the command SHALL also elaborate the worked example goal and close it with the entry.

#### Scenario: Checking a project's entries
- **WHEN** a project test file runs the check command over two valid entries and one whose Sage name is wrong
- **THEN** two entries pass, and the third fails with the elaboration or equality error

### Requirement: Discoverable entries
`sage -python -m veriphy.translations list` SHALL print every entry of the project's tables: the file, the Lean constant or lemma, the Sage name, and the conditions. `show <name>` SHALL print one entry in full. Both SHALL report invalid files without failing on them.

#### Scenario: Listing a project's entries
- **WHEN** `translations/` holds `hyperbolic.json` with `Real.cosh` and `Real.sinh`
- **THEN** `list` prints both entries with their file

### Requirement: Agent workflow for an unknown function
The `certify` playbook SHALL instruct the agent as follows. When a script's problem shows an opaque atom whose head is a function that Sage knows, the agent adds an entry to the project's `translations/`, runs the round-trip check, and only then relies on the entry. The playbook SHALL instruct the agent never to edit Veriphy's core tables for this.

#### Scenario: Agent meets `Real.cosh`
- **WHEN** an agent's goal contains `Real.cosh x` and the problem shows `Real.cosh x` as an atom
- **THEN** the playbook leads the agent to write `translations/cosh.json`, check it, and rerun the script with `cosh(x0)` in the symbolic form
