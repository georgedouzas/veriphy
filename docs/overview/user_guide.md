# Guide

Veriphy verifies claims in any field that has a checkable notion of evidence. The framework knows nothing about
any particular field: its packs bring the tools, the checks and the levels. This guide covers the framework. The
[packs](../packs/index.md) pages cover what each shipped pack adds. To install Veriphy, see the [README](../index.md).

## Concepts

| Concept | What it is |
|---|---|
| claim | something a source asserts: a theorem, an estimate, a convention a chapter relies on |
| primitive | a deterministic operation, typed by JSON Schema, pinned, of one trust class; it records nothing |
| step | a primitive with declared inputs; running it writes a record, and the same inputs replay it |
| record | what a step checked: the digest of its inputs, the tools and versions, the status, the outputs, the level |
| trust class | the kind of evidence a primitive gives: `kernel`, `checker`, `reproduction`, `oracle`, `measurement`, `search` |
| level | how verified a claim is, in one order from `none`, each level of one trust class |
| workflow | a list of steps with what each status does next; the records decide the next step |
| agent | writes what Veriphy cannot (a formal statement, a proof, an extraction), and records it with an agent step |
| pack | a directory with a `pack.yaml` that adds to any of the above |

Agents and computer algebra systems are untrusted. A step's trust class comes from the primitive that decides it, so
an agent's artifact counts only once a checking step accepts it, and a search tool's answer counts only through the
checker that verifies it.

## The layers

![The layers](../architecture/diagrams/layers.svg)

Veriphy is built in five layers, each using only the ones below it, and each with its own group of commands. A pack can
add to every layer, so a field is added without changing Veriphy.

| Layer | Holds | Command | A pack adds |
|---|---|---|---|
| 4. Agents | playbooks and skills: what an agent writes, and in which workflow | `veriphy layers agents` | playbooks, recipes, skills |
| 3. Workflows | step sequences as data; the records decide the next step | `veriphy layers workflow` | workflows |
| 2. Claims | the claim graph: each claim's level from the records, effective levels, clashes | `veriphy layers claims` | levels, conventions |
| 1. Steps | a primitive with declared inputs, replayed by their digest, and recorded | `veriphy layers step` | steps, digest scopes |
| 0. Primitives | deterministic operations, typed, pinned, of one trust class, recording nothing | `veriphy layers primitive` | primitives, tools |

Under them all, `veriphy.yaml` selects the packs (`veriphy pack list`) and can override any entry they declare
(`veriphy config show`). The [architecture](../architecture/index.md) explains the design.

## The workspace

A workspace is a directory, usually a repository. Veriphy finds its root by walking up from the current directory, or
takes it from `--root`. It keeps its files under `.veriphy/`:

| Directory | Holds |
|---|---|
| `.veriphy/runs/` | the records, one JSON file per step run; they stay out of git, and deleting them only means the steps run again |
| `.veriphy/graph/` | the claim graph: `sources/`, `lean/`, `runs/` and `appendix/` |

A pack may add directories of its own; the `math` pack's are on [its page](../packs/math.md#your-project).

### `veriphy.yaml` and packs

The workspace may hold `veriphy.yaml` at its root. Every key is optional. Without the file, a workspace is
`packs: [math]`, which brings in `lean` and `core`.

```yaml
version: 1
packs: [reproduction, ./packs/econ]   # by name, or by the path of a directory holding a pack.yaml
tools:
  r: {timeout: 1200}
```

A pack is named by the name of a shipped pack, by the name a Python package registers under the `veriphy.packs` entry
point, or by path. Packs are applied in order, each after the packs it requires, then the workspace file, each as a
JSON Merge Patch (RFC 7396): a mapping merges key by key, a later value replaces an earlier one, and `null` removes an
entry. So `tools: {sage: null}` drops SageMath and every primitive that needs it. When two packs that do not require
each other define the same entry, `veriphy config check` names both, and the workspace file settles it by defining the
entry itself.

`veriphy config show` prints the resolved configuration with the pack or file each entry comes from.
`veriphy config check` refuses collisions and references that do not resolve. The digest of the resolved configuration
goes into every record, so a changed pin makes the steps run again, and a changed comment does not.

## Commands

```text
veriphy layers primitive list | describe | run          layer 0
veriphy layers step <step> … | list | records           layer 1
veriphy layers claims validate | reason | levels | …    layer 2
veriphy layers workflow list | next | run               layer 3
veriphy layers agents list | path | show | copy         layer 4
veriphy config show | check
veriphy pack list | <pack> <program> …
veriphy help
```

`veriphy help` lists the workspace's steps, its packs' programs and Lean's verbs. Every command takes `--help`. Python
runs a step as `veriphy.run(step, target, **inputs)`.

## Scenarios by layer

Each scenario runs in a workspace with no `veriphy.yaml`, so it has the default packs (`core`, `lean`, `math`), unless
it says otherwise. The output shown is what the command prints.

### Layer 0: run a primitive by hand

A primitive is the smallest thing Veriphy runs. Running one by hand writes no record, which makes it the way to see
what a tool does with an input:

```sh
veriphy layers primitive list                      # name, trust class, pack, whether it can run here
veriphy layers primitive describe sage.sample      # its tool, its pin, its input and output schemas
echo '{"data": "claims.nt", "shapes": "shapes.ttl"}' > input.json
veriphy layers primitive run shacl.validate --input input.json
# {"conforms": false, "violations": [{"focus": "<urn:c1>", …}], "tools": [{"name": "veriphy", …}]}
```

An input that breaks the schema is refused before the tool starts, naming the field. A tool whose version differs from
its pin is refused, naming both versions.

### Layer 1: run a step, and replay it

A step runs a primitive on declared inputs and records the result:

```sh
veriphy layers step check Claim.lean
# check: accepted
# .veriphy/runs/check/3f9c….json
veriphy layers step check Claim.lean                # nothing that Claim.lean imports changed
# check: accepted (replayed)
veriphy layers step check Claim.lean --json         # the record itself: each declaration's axioms, the tools
veriphy layers step records                         # every record: step, status, digest
```

The second run starts no Lean: the digest of the inputs matches a record, which is returned as it is. `--rerun` runs
anyway. The exit status is 0 when the step accepted, 1 when it refused, 2 on bad usage and 3 when the result is
unchecked.

### Layer 2: read what the records establish

Claims sit in the claim graph, and each claim's level comes from the records that name it:

```sh
veriphy layers claims validate                      # the extracted claims against the shapes
veriphy layers claims reason                        # the consequences, checked by oo-horn: entailed
veriphy layers claims levels --source chapter3      # each claim's own level, effective level, what caps it
veriphy layers claims impact chapter3 parallel      # every claim that rests on the convention `parallel`
```

A claim's effective level is the lowest level among everything it rests on, and every level is shown with its trust
class, such as `reproduced (reproduction)` or `certificate (kernel)`.

### Layer 3: let the workflow choose the next step

A workflow reads the target's records and names the next step, the same way every time for the same records:

```sh
veriphy layers workflow list
# prove-claim    formalize, meaning, check, prove, check
# verify-paper   extract, validate, reason, report
veriphy layers workflow next prove-claim Claim.lean
# formalize (an agent step): an artifact to record
veriphy layers step formalize Claim.lean --by agent
veriphy layers workflow run prove-claim Claim.lean --input declaration=t
# meaning: agrees
# check: accepted
# prove-claim: waiting for prove: record the artifact, as veriphy layers step prove Claim.lean
```

`run` runs every step that needs no agent and stops at the first that does. A counterexample from `meaning` stops the
workflow, and a refused `check` goes back to `formalize`, up to its `attempts`.

### Layer 4: give an agent its playbook

Agents follow playbooks that ship with the packs:

```sh
veriphy layers agents list                          # every playbook, recipe, template and asset
veriphy layers agents path                          # their directory, for any agent
veriphy layers agents show recipes/sos              # one recipe
veriphy layers agents copy recipes/templates/sos    # a template into the workspace, to edit
```

In Claude Code, the skills do the same: `/veriphy:prove`, `/veriphy:research` and `/veriphy:reproduce` ask
`veriphy layers workflow next` for the step, write the artifact when it is theirs, record it, and run the rest.

## Scenarios by pack

### `core`: check how a chapter's claims fit together

The `core` pack needs neither Lean nor SageMath. With `packs: [core]` in `veriphy.yaml`, an agent extracts a chapter's
claims, conventions and dependencies to `.veriphy/graph/sources/chapter3.agent.ttl`, and:

```sh
veriphy layers step extract .veriphy/graph/sources/chapter3.agent.ttl --by agent
veriphy layers step validate                        # validate: conforms
veriphy layers step reason                          # reason: entailed
veriphy layers claims clashes                       # a claim resting on parallel and on no-parallel trends
veriphy layers step report chapter3 --format latex  # report: written, .veriphy/graph/appendix/chapter3.tex
```

Every claim's level is `none` here, since `core` grants none: the graph reports structure, clashes and impact, and the
other packs add the evidence.

### `lean`: check a Lean file and read its levels

```sh
veriphy layers step check Claim.lean                # accepted, with each declaration's axioms
veriphy layers step level MyProject.Basic           # each declaration under the module, with its level
```

A complete proof on the standard axioms reads `lean-proof`; one that uses `sorry` or another axiom reads `none`. See
[the `lean` pack](../packs/lean.md).

### `math`: test a statement, certify a goal, prove a claim

Test that a formal statement says what was meant, before proving it:

```sh
veriphy layers step meaning Claim.lean wrong --informal "the square root of x squared is -x"
# meaning: counterexample                           (the record holds x = 1, lhs 1, rhs -1)
```

Close a computational goal with a certificate Sage finds and the kernel checks, inside the Lean file:

```lean
example (a b : ℝ) : 0 ≤ a ^ 2 * b ^ 2 - 2 * a * b + 1 := by
  veriphy certify "return found(nlinarith([sq_nonneg(x0*x1 - 1, problem)]))"
-- Try this: nlinarith [sq_nonneg (a * b - 1)]
```

Commit the Sage-free replacement. `veriphy pack math certificates list` shows the scripts saved in the project for
reuse, and the `prove-claim` workflow (above) runs the whole proof. See [the `math` pack](../packs/math.md).

### `reproduction`: reproduce a published estimate

With `packs: [reproduction]` in `veriphy.yaml`, podman or docker, and the paper's script and data:

```sh
veriphy layers step reproduce analysis.R mtcars.csv <sha256> --claimed -5.344472 --claim mpg-weight
# reproduce: agrees                                 (the record grants reproduced)
veriphy layers step vary analysis.R mtcars.csv <sha256> '["mpg ~ wt + hp", "mpg ~ wt + cyl"]' --claim mpg-weight
# vary: robust                                      (the record grants robust)
veriphy layers claims levels                        # mpg-weight: robust (reproduction)
```

Data whose SHA-256 differs from the claim's is refused before anything runs, and an estimate that differs is recorded
as `differs`, with both values. See [the `reproduction` pack](../packs/reproduction.md).

## Primitives

Under every step are primitives: deterministic operations that record nothing. A primitive has an input schema, an
output schema and a trust class, and runs one of two ways:

- as a Python function, in-process;
- as a command, run once per call, that writes one JSON result to `{out}`: any other program, such as SageMath in the
  `math` pack or R in the `reproduction` pack.

Veriphy keeps no process alive between calls.

A tool is pinned by an exact version, a commit with its hash, or a container image by digest (run with podman or
docker). The input is checked against its schema before anything runs, the tool against its pin, and the output against
its schema. Every output names the tools that produced it, with their versions.

A composite combines primitives, and its trust class is that of the part that decides it. The `math` pack's `certify`
has Sage search for a proof and Lean check it, so its class is `kernel`.

```sh
veriphy layers primitive list                     # every primitive, its class, its pack, whether it can run here
veriphy layers primitive describe certify         # its parts, its deciding part, its schemas
veriphy layers primitive run shacl.validate --input input.json
```

## Steps and records

`veriphy layers step <step> <target> [inputs]` runs a step and prints its status and the path of its record.
`veriphy layers step list` lists the workspace's steps with the pack that defines each, and `veriphy layers step <step>
--help` is generated from the step's declaration.

A record is a JSON file under `.veriphy/runs/<step>/<digest>.json`. It holds the step, its kind, the digest of its
inputs, the tool versions, the status, the outputs and any level granted. The digest covers the content of the inputs,
not their paths, so a step that runs again on the same inputs returns its record without running anything. A record
whose status is `unchecked` or `failed` describes the machine rather than the inputs, so the step runs again next
time. `--rerun` forces a run, and keeps both records when the result changed.

`--json` prints the record and nothing else, for agents. The command exits with status 0 when the step accepted, 1
when it refused, found a counterexample or failed, 2 on bad usage, and 3 when the result is unchecked or undecided.
`veriphy layers step records` lists the records, and `records <digest>` shows one.

Python gets the same result, with its `verb`, `target`, `status`, `outputs`, `level` and `record`:

```python
import veriphy

result = veriphy.run('reproduce', 'analysis.R', data='mtcars.csv', sha256='450a…', claimed=-5.344472)
result.status, result.level   # ('agrees', 'reproduced')
```

Steps come in four kinds: `agent` (records an artifact an agent wrote, with its author), `evidence` (a measurement,
granting no level), `check` (accepts or refuses, and may grant a level) and `derived` (computed from other records).

### Declaring a step

A step over a primitive is declared in YAML, in a pack's `pack.yaml` or in `veriphy.yaml`, with no Python:

```yaml
steps:
  reproduce:
    kind: check
    primitive: r.run
    grants: reproduced
    compare: {field: estimate, against: claimed, tolerance: 0.000001}
    inputs:
      script: {scope: file, path: true, help: the analysis script}
      data: {scope: file, path: true}
      sha256: {help: "the data's SHA-256, as the claim names it"}
      claimed: {type: number, optional: true, record: true}
```

| Field | Meaning |
|---|---|
| `kind` | `agent`, `evidence`, `check` or `derived` |
| `primitive` | the primitive the step calls (none for an agent step) |
| `inputs` | one argument or option each, in order |
| `status` | the output field that holds the status (default `status`) |
| `compare` | sets the status to `agrees` or `differs`, comparing an output `field` with an input `against`, within a `tolerance` |
| `grants` | the level the step grants when it accepts |
| `seed` | whether the step takes `--seed`, which enters the digest |
| `help` | one line for the command's help |

An input has a digest `scope`: `value` (the default), `file`, `files`, or one a pack defines. For example, the `lean`
pack's `lean-imports` covers a Lean file, the workspace files it imports, the toolchain and the manifest, so an edit to
an unrelated file replays the record. An input may also be a `path` (resolved from the workspace root), `optional` (an
option, not an argument), of a `type` (`string`, `integer`, `number` or `json`), with a `default`, `many` (repeatable),
or `record` only (kept in the record, not sent to the primitive).

An agent step needs no primitive:

```yaml
steps:
  formalize:
    kind: agent
    inputs: {artifact: {scope: file, path: true}}
```

`veriphy layers step formalize Claim.lean --by agent` records the file's digest and its author.

## Trust classes and levels

| Class | Evidence | Grants levels |
|---|---|---|
| `kernel` | a proof checked by a proof assistant's kernel | yes |
| `checker` | a result checked by an independent verified checker | yes |
| `reproduction` | the same result recomputed from the same code, data and environment | yes |
| `oracle` | an exact or interval evaluation by an untrusted system | yes |
| `measurement` | a report about the inputs, such as a validation | no |
| `search` | a candidate found by search, which something else must check | no |

The classes are fixed. The levels come from the packs: each names its class and the level directly below it, and a
workspace's levels form one order from `none`. With the default packs the order is `none`, `oracle-test`,
`kernel-test`, `lean-proof`, `certificate`. With `reproduction` it gains `reproduced` and `robust`. When two packs place
a level in the same position, `veriphy config check` names both, and `veriphy.yaml` orders them by overriding `above`.

A step grants only levels of its primitive's class. `veriphy config check` refuses a step that would grant another,
and so does the step itself when it writes its record. Every report shows a level with its class, as in
`reproduced (reproduction)`, so a reproduction or an oracle test never reads as a proof.

## Workflows

A workflow is a list of steps in a pack's `pack.yaml` or in `veriphy.yaml`, with what a record's status does next:

```yaml
workflows:
  prove-claim:
    - formalize
    - meaning: {counterexample: stop}
    - check: {refused: formalize, attempts: 3}
    - prove
    - check: {refused: prove, attempts: 5}
```

`veriphy layers workflow next prove-claim Claim.lean` reads the records whose inputs name the target, in the order
they were written, and names the next step: the first entry with no newer record, or `stop` with the status that
stopped it. Going back to an earlier entry needs a new record there. `attempts` counts the step's records, and
`exhausted` names where to go once they are used up (`stop` by default). `when: {without: kernel}` runs an entry only
while no record grants a level of the `kernel` class.

`veriphy layers workflow run prove-claim Claim.lean --input declaration=t` runs the steps that are not an agent's
until the next one is, and says what the agent must record. `veriphy layers workflow list` lists the workspace's
workflows. The `math` pack ships `prove-claim` and `verify-paper`, and the `reproduction` pack `reproduce-analysis`.

## The claim graph

Steps check one claim at a time. The claim graph checks how the claims of a paper or research program fit together:
which conventions each one assumes, which claims it rests on, and how verified it is once its weakest dependency
counts. It belongs to the `core` pack and works with any field's levels.

The reasoner is untrusted. `oo-horn`, a verified Lean checker from
[Open Ontologies](https://github.com/fabio-rovai/open-ontologies) that shares no code with Veriphy, accepts or refuses
every run, and Veriphy reports a conclusion of the graph only with the verdict the checker printed.

### Setup

```sh
pip install 'veriphy[graph]'
```

The first command that needs them sets up the reasoner and `oo-horn` from the pinned Open Ontologies release, says
what it fetches or builds, and caches it in `~/.cache/veriphy/open-ontologies/v2.1.0`:

- the release is cloned with `git`, and refused unless its commit is the pinned one;
- the reasoner is imported from the release's source, so nothing is installed into Python at run time;
- on Linux x86_64 `oo-horn` is the release's prebuilt binary, kept only if its SHA-256 matches both the pinned hash and
  the hash the release lists, and only if it runs;
- elsewhere `oo-horn` is built once with the release's Lean toolchain through `elan`, which takes minutes.

`veriphy layers claims checker build` does the same ahead of time. `VERIPHY_GRAPH_SETUP=off` forbids automatic setup,
for offline machines and CI, and `VERIPHY_OO_HORN` names a binary to use. Without a checker, every result is labelled
`unchecked`, with the command that sets it up.

### Sources

Each source has one Turtle file per provenance in `.veriphy/graph/sources/`: `chapter9.agent.ttl` for what an agent
extracted, and `chapter9.human.ttl` for what a person wrote or confirmed. An agent never writes a `.human.ttl` file.

```turtle
@prefix vp: <urn:veriphy:vocabulary#> .
@prefix : <urn:veriphy:source:chapter3#> .

:parallel a vp:Convention ; vp:conventionFor "identification" ; vp:statement "parallel trends" .
:est-1 a vp:Claim ; vp:statedIn :chapter3 ; vp:statement "The policy lowered unemployment by 2.1 points." ;
    vp:assumes :parallel .
:policy a vp:Claim ; vp:statedIn :chapter3 ; vp:statement "The policy should be extended." ;
    vp:uses :est-1, <urn:veriphy:source:doi:10.1257/aer.20181169#table-2> .
```

A claim from another paper is a node of that paper's source, named by its arXiv identifier or DOI. `owl:sameAs` says
that two sources mean the same concept.

```sh
veriphy layers claims vocabulary                              # print the vocabulary
veriphy layers claims validate                                # check the files against the shapes
veriphy layers claims confirm chapter3 est-1 assumes parallel   # move one triple to the human file
```

`validate`'s SHACL report is a measurement, not a checked conclusion.

### Levels in the graph

A claim's own level is the highest level it earns: from a record of a step whose inputs name it (`--claim est-1` on
`reproduce`), or from the formal claim that formalizes it (the `lean` pack's `#veriphy export`). It is `none`
otherwise. Its effective level is the lowest level among everything it uses, directly or not.
`veriphy layers claims levels --source chapter3` prints:

```text
| claim | own | effective | capped by | Lean |
|---|---|---|---|---|
| est-1 | robust (reproduction) | robust (reproduction) |  |  |
| lemma-2 | certificate (kernel) | certificate (kernel) |  | Econ.lemma2 |
| thm-3 | certificate (kernel) | reproduced (reproduction) | est-2 | Econ.thm3 |
```

Here the workspace selects `math` and `reproduction` and places `reproduced` and `robust` below `kernel-test` in its
`veriphy.yaml`. A claim proved in Lean that rests on an estimate that was only reproduced is then capped at
`reproduced`, and the report names the claim that caps it.

### Reasoning and verdicts

`veriphy layers claims reason` derives the consequences and writes a certificate under
`.veriphy/graph/runs/<digest>/`: the asserted triples, the rules, one derivation line per conclusion, and a digest.
Veriphy states the meaning of its vocabulary as OWL axioms that the checker's built-in rules evaluate. Every run
therefore uses the built-in rule table unchanged, and an accepted run earns `entailed` through the theorem
`OOCert.entails_of_builtin_horn`: every conclusion holds in every model of the asserted triples.

| Status | Meaning |
|---|---|
| `entailed` | the checker accepted the run, and the verdict is its own word |
| `rejected` | the checker refused a derivation line, and names it |
| `unchecked` | no checker was found or it didn't finish, and no conclusion is reported as checked |
| `incomplete` | the run stopped before its fixpoint |

`veriphy layers claims recheck .veriphy/graph/runs/<digest>` checks a stored run again without the reasoner, and says
whether the current graph still asserts the same triples. The commands exit with status 3 when the checker didn't
accept the run. The `reason`, `validate` and `report` steps run the same operations and record them.

### Conventions, impact and clashes

Conventions of the same aspect exclude each other. A pack declares the aspects it knows: the `reproduction` pack has
`identification: [parallel-trends, no-parallel-trends]`. `veriphy layers claims excludes` proposes the `excludes`
triples, and `--confirm` writes them as human assertions. `veriphy layers claims clashes` then reports every claim
with two checked `assumes` conclusions whose conventions exclude each other, including assumptions inherited across
papers.

`veriphy layers claims impact chapter3 parallel` lists every claim that assumes the convention, directly or through
its dependencies, with the chain that reaches it. Before changing a convention, edit the source file and compare with
the last commit:

```sh
veriphy layers claims plan --against HEAD
```

The plan reasons over both graphs, has both runs checked, and lists the assertions you changed and the consequences
added and removed: `assumes` triples, level caps and clashes.

### Slices and the appendix

`veriphy layers claims slice chapter3 policy` prints what an agent needs to work on a claim: its statement, the
statements and levels of the claims it uses, and each convention it assumes. Veriphy reasons over the slice alone, has
that run checked, and offers the slice only if it keeps every consequence about the claim.

`veriphy layers claims appendix chapter3 --format latex` writes `.veriphy/graph/appendix/chapter3.tex`: a row per
claim with its own and effective levels, what caps it, and its clashes, and a paragraph with the run, the verdict, the
provenance of the assertions and the command that rechecks it. An unchecked run says so. `--format markdown` writes the
same as Markdown.

### Limits

- The graph doesn't check that a prose claim and its formal statement say the same thing. `formalizedBy` is an
  assertion, and reports count where each assertion came from.
- A checked conclusion is only as good as the asserted triples. A bad extraction gives a faithfully wrong conclusion.
- No clash found is the reasoner's result, not a checked conclusion. A Horn certificate proves what was derived, not
  what wasn't.

## Agents and skills

Playbooks are plain Markdown in each pack's `agents/` directory, installed with the Python package. Any agent can
follow them: `veriphy layers agents path` prints the directory (`--pack reproduction` for that pack's),
`veriphy layers agents list` names every playbook, recipe, template and asset, and `veriphy layers agents copy`
copies a template into the workspace.

The Claude Code skills are thin wrappers that follow a workflow: they ask `veriphy layers workflow next` for the step,
do it if it is theirs, record it with an agent step, and let `veriphy layers workflow run` do the rest.

| Skill | Pack | Workflow |
|---|---|---|
| `prove` | `math` | `prove-claim` |
| `certify` | `math` | one goal, inside `prove` |
| `research` | `math` | `verify-paper` |
| `reproduce` | `reproduction` | `reproduce-analysis` |

## Writing a pack

A pack is a directory with a `pack.yaml`. A local pack is named in `veriphy.yaml` by its path. A pack published as a
Python package declares an entry point in the `veriphy.packs` group, naming the module that holds its `pack.yaml`.
Then `packs: [<name>]` selects it.

```yaml
version: 1
name: econ
requires: [core]          # packs applied first; their entries may be overridden here
```

Every other section is optional:

| Section | Declares |
|---|---|
| `tools` | external programs, each a command run once per call (`contract: files`): `run`, `pin` (`version`, `commit` with `sha256`, or `image`), `version`, `timeout` |
| `primitives` | `function: module:attribute`, or `tool` with a `command` (its arguments, with `{input}`, `{out}`, `{seed}` and `{file:<input>}`); `trust`, `input` and `output` schemas; `{composite: module}` for one written in Python |
| `scopes` | digest scopes, each `{function: module:attribute}` taking the workspace root and the value |
| `steps` | steps over primitives, or agent steps; `{code: module}` for one written in Python |
| `levels` | each with `trust`, `above` and `description` |
| `conventions` | aspects and the conventions that exclude each other |
| `workflows` | step sequences with transitions |
| `commands` | programs as `{command: module:attribute, help}`, run as `veriphy pack <pack> <name>` |

Playbooks go in the pack's `agents/` directory. Python code a pack declares (functions, composites, scopes, commands)
is imported only when used, so a pack whose tools are missing still loads, and `veriphy layers primitive list` says
what can't run.

`veriphy config check` reports collisions with other packs, steps naming primitives or scopes no pack declares,
levels outside one order, steps granting a level their primitive's class can't grant, and workflows naming unknown
steps. The [reproduction pack](https://github.com/georgedouzas/veriphy/tree/main/src/veriphy/packs/reproduction) is a
complete example outside mathematics: one tool pinned by image, two composites, two steps, two levels, a convention,
a workflow, a playbook and a worked example.

## Environment variables

| Variable | Effect |
|---|---|
| `VERIPHY_GRAPH_SETUP` | `off` stops the claim graph fetching or building anything |
| `VERIPHY_OO_HORN` | use this `oo-horn` binary |
| `VERIPHY_SAGE_CMD` | the `sage` executable, if it isn't on `PATH` (the `math` pack) |
| `VERIPHY_SAGE_TIMEOUT` | seconds allowed per Sage request, 150 by default (the `math` pack) |
