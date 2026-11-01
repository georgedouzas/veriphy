# research/certified-graph-reasoning Specification

## Purpose
Derives the consequences of a research graph with an untrusted reasoner and has every consequence checked by a
verified Lean checker that shares no code with Veriphy, so a graph conclusion is reported only with the checker's
verdict.

## Requirements

### Requirement: Vocabulary axioms on the built-in rules
Veriphy SHALL state the meaning of its vocabulary as OWL axioms that the checker's built-in rules evaluate: `assumes`
follows `uses`, `owl:sameAs`, `formalizedBy` and `realizedBy`, and level caps follow `uses`, `formalizedBy` and the
level order. Every
run SHALL use the built-in rule table unchanged and SHALL NOT add a rule.

#### Scenario: Reading the axioms
- **WHEN** a user asks the graph CLI for the vocabulary axioms of a graph
- **THEN** it prints the generated axioms, each with the convention or level it is about

#### Scenario: A transitive assumption
- **WHEN** the graph states `a uses b`, `b uses c` and `c assumes k`
- **THEN** reasoning derives `b assumes k` and `a assumes k`, and every derivation line names a built-in rule

### Requirement: Certificate for every run
Every reasoning run SHALL write a certificate directory under `.veriphy/graph/runs/<run>/` with the asserted
triples, the generated axioms among them, the rule table, one derivation line per derived triple in the format
`oo-horn` reads, and a digest of the asserted triples. A run that does not reach a fixpoint SHALL be reported as
incomplete.

#### Scenario: A complete run
- **WHEN** a user runs reasoning over a graph of 40 claims
- **THEN** `.veriphy/graph/runs/<run>/` holds the asserted triples, the rules, the derivations and the digest, and
  the report gives the numbers of asserted and derived triples

#### Scenario: An iteration limit
- **WHEN** the run reaches its iteration limit before a fixpoint
- **THEN** the report says the run is incomplete, and no conclusion of the run is reported as checked

### Requirement: Checked by oo-horn
After each run, Veriphy SHALL run `oo-horn` on the certificate. A conclusion SHALL be reported as checked only when
the checker accepted the certificate, and the verdict word SHALL be copied from the checker's report. Veriphy SHALL
NOT write a verdict word itself.

#### Scenario: Accepted
- **WHEN** `oo-horn` accepts the certificate of a run
- **THEN** the report shows the verdict `entailed` and the theorem `OOCert.entails_of_builtin_horn`, both as the
  checker printed them

#### Scenario: A forged derivation
- **WHEN** a derivation line of a run is edited to conclude `a assumes k2` from premises that do not support it
- **THEN** the check reports the run as rejected, with the line, the rule and the premises the checker printed, and
  no conclusion of the run is reported as checked

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

### Requirement: Rechecking a stored run
The graph CLI SHALL recheck a stored run directory without the reasoner, and SHALL report whether the run's digest
still matches the current graph.

#### Scenario: Rechecking later
- **WHEN** a reviewer rechecks a run directory from an earlier commit
- **THEN** the CLI reports the checker's verdict for it, and says whether the current graph still has the same
  asserted triples

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
