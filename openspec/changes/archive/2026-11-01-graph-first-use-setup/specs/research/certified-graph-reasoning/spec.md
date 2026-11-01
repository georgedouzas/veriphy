# Spec Delta

## MODIFIED Requirements

### Requirement: No checker, no verdict
When `oo-horn` is not found, cannot be set up, or does not finish, Veriphy SHALL report the run as unchecked, say why,
and give the command that sets the checker up. Its conclusions SHALL be shown only under the word `unchecked`.

#### Scenario: Checker missing
- **WHEN** reasoning runs on a machine without `oo-horn`
- **THEN** the report marks every conclusion `unchecked`, names the paths it searched, and prints the build command

#### Scenario: Setup failed
- **WHEN** first-use setup cannot fetch the release or build the checker
- **THEN** the report marks every conclusion `unchecked`, gives the failing step and its output, and prints the build
  command

### Requirement: Building the checker
The graph CLI SHALL set up `oo-horn` from the Open Ontologies release that Veriphy pins, into a cache outside the
project: the release's prebuilt binary where the release ships one for the platform, else a build with the release's
own Lean toolchain. The reasoner SHALL come from the same release. An explicit checker path SHALL take precedence.

#### Scenario: First build
- **WHEN** a user runs the checker build command on a machine with `elan` and `git`
- **THEN** the pinned release is fetched, the checker is downloaded or built, the reasoner of that release is ready,
  and the command prints the path of `oo-horn`, the release and its commit

#### Scenario: Prebuilt checker
- **WHEN** the checker is set up on Linux x86_64
- **THEN** the release's prebuilt `oo-horn` is downloaded, and it is used only when its SHA-256 equals the hash Veriphy
  pins and the hash the release's `SHASUMS.txt` lists

#### Scenario: A tampered download
- **WHEN** the downloaded binary's SHA-256 differs from the pinned hash
- **THEN** the binary is deleted, setup fails naming both hashes, and no run uses it

#### Scenario: An explicit checker
- **WHEN** the environment names a path to `oo-horn`
- **THEN** reasoning uses that binary and reports its path

## ADDED Requirements

### Requirement: Setup on first use
The first graph command that needs the reasoner or the checker SHALL set up the missing one from the pinned release
before it runs, print what it fetches or builds and where, and cache it, so installing the graph extra is the only
installation step. A later command SHALL find the cache and set up nothing.

#### Scenario: First reasoning run after installation
- **WHEN** `python -m veriphy.graph reason` runs right after `sage -pip install 'veriphy[graph]'`
- **THEN** it reports that it is setting up the reasoner and the checker, sets them up, and reports the run with the
  checker's verdict

#### Scenario: Second run
- **WHEN** the same command runs again
- **THEN** it sets up nothing and prints no setup message

### Requirement: Reasoner from the cached release
The reasoner SHALL be imported from the cached release source. Veriphy SHALL NOT install packages into the Python
environment at run time.

#### Scenario: A clean interpreter
- **WHEN** the reasoner is set up on first use
- **THEN** the interpreter's installed packages are the same before and after, and the reasoner imports from the cache

### Requirement: Pinned release commit
Veriphy SHALL pin the commit of the Open Ontologies release, and SHALL refuse a fetched release whose commit differs.

#### Scenario: A moved tag
- **WHEN** the pinned tag points to a different commit than the one Veriphy pins
- **THEN** setup fails naming both commits, and nothing from that fetch is used

### Requirement: Turning automatic setup off
When `VERIPHY_GRAPH_SETUP` is `off`, Veriphy SHALL set up nothing on first use. A missing checker SHALL then give an
unchecked run, and a missing reasoner SHALL give an error that names the setup command.

#### Scenario: Offline continuous integration
- **WHEN** `VERIPHY_GRAPH_SETUP=off` and no checker is cached
- **THEN** reasoning reports the run `unchecked`, makes no network request, and prints the setup command
