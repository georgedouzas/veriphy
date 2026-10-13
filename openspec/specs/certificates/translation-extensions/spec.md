# certificates/translation-extensions Specification

## Purpose
Organizes translation and rewrite entries in namespaces by library (the mathlib core, library packs such as Physlib, and the project). It lets a project extend the translation with entries Veriphy does not cover, checked by a round trip, with no Veriphy release.

## Requirements

### Requirement: Table namespaces by library
Entries SHALL belong to one of three namespaces:
- `mathlib`: the core, which refers only to Lean core and mathlib constants and is always active;
- a library pack named for its library, such as `physlib`, shipped with Veriphy as data;
- `project`: the entries in the project's `.veriphy/translations/`.

A library pack SHALL be active only when the elaboration environment contains its library's root module. Veriphy SHALL NOT import any library other than mathlib.

#### Scenario: Physlib pack inactive without Physlib
- **WHEN** a project that does not depend on Physlib extracts a problem
- **THEN** no `physlib` entry is loaded, and no Physlib constant is looked up

#### Scenario: Physlib pack active
- **WHEN** a project importing Physlib has a goal with `∂ₜ x t`
- **THEN** the `physlib` pack translates it as the derivative of `x` at `t`, and the problem names the pack the entry came from

### Requirement: Library-specific recipes
Recipes and recipe assets specific to a library SHALL live under `prompts/recipes/<library>/`, be indexed in their own section of the recipe index, and be offered only when that library's pack is active.

#### Scenario: Physlib recipe offered
- **WHEN** the `physlib` pack is active and the goal concerns Physlib's `lorentzAlgebra`
- **THEN** the recipe index offers the Physlib Lorentz-algebra recipe alongside the generic `lie_structure`

### Requirement: Entries live in the project
Translation entries SHALL be JSON files in `.veriphy/translations/` at the project root, as defined by the project layout. Each file SHALL be validated against a declared schema. An invalid file SHALL be reported naming the file and the field, and SHALL NOT be loaded.

#### Scenario: Invalid entry
- **WHEN** `.veriphy/translations/cosh.json` lacks its Sage name
- **THEN** extraction reports `.veriphy/translations/cosh.json: missing field 'sage'` and the other entries still load

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
An entry SHALL NOT redefine an entry of the same or an earlier namespace (`mathlib`, then library packs, then `project`). A conflict SHALL be reported naming both entries and their namespaces, and the later entry SHALL NOT be loaded.

#### Scenario: Conflict with the core
- **WHEN** a project entry maps `Real.exp` to a different Sage name
- **THEN** extraction reports the conflict with the core entry for `Real.exp`, and the core entry stays in force

### Requirement: Round-trip check
A Lean command SHALL check every project entry. For each entry it translates the round-trip example, renders it back through the daemon, and proves the rendering equal to the original. It reports each entry as passed or failed, with Lean's error for a failure. For each rewrite entry, the command SHALL also elaborate the worked example goal and close it with the entry.

#### Scenario: Checking a project's entries
- **WHEN** a project test file runs the check command over two valid entries and one whose Sage name is wrong
- **THEN** two entries pass, and the third fails with the elaboration or equality error

### Requirement: Discoverable entries
`sage -python -m veriphy.translations list` SHALL print every entry of the active namespaces: its namespace, the file, the Lean constant or lemma, the Sage name, and the conditions. `show <name>` SHALL print one entry in full. Both SHALL report invalid files without failing on them.

#### Scenario: Listing a project's entries
- **WHEN** `.veriphy/translations/` holds `hyperbolic.json` with `Real.cosh` and `Real.sinh`
- **THEN** `list` prints both entries with their file, under the `project` namespace

### Requirement: Agent workflow for an unknown function
The `certify` playbook SHALL instruct the agent as follows. When a script's problem shows an opaque atom whose head is a function that Sage knows, the agent adds an entry to the project's `.veriphy/translations/`, runs the round-trip check, and only then relies on the entry. The playbook SHALL instruct the agent never to edit Veriphy's core tables for this.

#### Scenario: Agent meets `Real.cosh`
- **WHEN** an agent's goal contains `Real.cosh x` and the problem shows `Real.cosh x` as an atom
- **THEN** the playbook leads the agent to write `.veriphy/translations/cosh.json`, check it, and rerun the script with `cosh(x0)` in the symbolic form
