## ADDED Requirements

### Requirement: Documentation structure

The documentation SHALL follow this order, with each page in plain words for a reader new to Veriphy:

- a home page that says in a few sentences what Veriphy does, shows one check, and links onward;
- an installation page;
- a getting-started tour;
- a tutorial that uses every command on one example;
- a user guide in numbered chapters;
- a command reference generated from the CLI;
- a configuration reference;
- the pack pages.

A term SHALL be explained where it first appears.

#### Scenario: A new reader finds a first check

- **WHEN** a reader opens the home page
- **THEN** it shows a command, its output, and one sentence on what the output means, before it introduces packs or
  levels

### Requirement: Executed console sessions

The console sessions of the getting-started tour, the tutorial, the user guide and the pack pages SHALL be run by the
test suite in page order. Each printed output SHALL match the command's real output, where `…` stands for any text and
a run of spaces or tabs for one space.

#### Scenario: A stale output fails the tests

- **WHEN** a step's printed summary changes and the tutorial still shows the old one
- **THEN** the documentation test fails and names the command

### Requirement: Session workspaces

The overview pages' sessions SHALL run in a workspace made from the example study. A pack page's sessions SHALL run
in a workspace that selects the pack and holds its examples. The `math` page's sessions need a Lean project and SHALL
NOT run. A session that needs the claim graph's checker or SageMath SHALL be skipped only where that is not set up.

#### Scenario: A pack page runs in its own workspace

- **WHEN** the test runs the `genomics` page
- **THEN** its commands run in a workspace whose `veriphy.yaml` selects `genomics` and which holds the genomics
  example files

### Requirement: Every command in the tutorial

Every command of the CLI that runs without the `math` pack SHALL appear in the tutorial, and the `math` pack's
commands SHALL appear on its page. A test SHALL enumerate the CLI's commands and fail on any the documentation omits.

#### Scenario: A new command without documentation

- **WHEN** a command is added to the CLI and no page uses it
- **THEN** the coverage test fails and names it

### Requirement: Generated command reference

The command reference SHALL be generated at build time from the CLI: for every command, its usage line, its help, and
its options with their help. A step's entry SHALL come from the shipped packs' declarations.

#### Scenario: An option changes

- **WHEN** a command gains an option
- **THEN** the next documentation build lists it without a hand edit
