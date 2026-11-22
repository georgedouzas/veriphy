# Guide

This guide explains how Veriphy works: what a check records, what a level means, how workflows decide the next step,
and how the claim graph puts claims together. [Getting started](getting_started.md) shows it in use, the
[packs](../packs/index.md) pages cover each field, and the [reference](reference.md) lists every command.

## The idea

A paper or a project makes claims. Veriphy checks each claim with a tool suited to it, and keeps a record of the check:
its inputs, the tools and their versions, and the result. From the records, each claim gets a level that says how far
it is verified and by what kind of evidence. The claim graph then combines the levels: a claim is only as verified as
the weakest claim it rests on.

Neither agents nor search tools are trusted. An agent's formal statement counts once Lean accepts it, Sage's candidate
proof counts once the Lean kernel checks it, and a paper's estimate counts once its own analysis reproduces it.

## Words

| Word | Meaning |
|---|---|
| claim | something a source asserts: a theorem, an estimate, a quotation, a measure of a construct |
| step | one check, run on declared inputs and recorded: `check`, `sample`, `reproduce`, `recompute` |
| record | what a step checked and found: its inputs' digest, the tools and their versions, the status, the outputs, the level |
| level | how far a claim is verified, such as `lean-proof` or `reproduced`; the levels form one order from `none` |
| trust class | the kind of evidence behind a level: `kernel`, `checker`, `reproduction` or `oracle` |
| convention | a choice a claim assumes, such as a measure or an identification assumption; choices of one aspect exclude each other |
| workflow | an ordered list of steps; the records decide which comes next |
| pack | a field's steps, tools, levels, conventions and workflows, declared in a `pack.yaml` |
| workspace | the directory Veriphy works in, with its `veriphy.yaml` or a Lean project's lakefile |

## Steps and records

A step runs one check and records it:

```console
$ veriphy layers step reproduce analysis.py survey.csv --claimed 0.127 --claim trust-education
reproduce analysis.py: agrees
  found 0.1265132608543874, the claim says 0.127 (tolerance 0.0005)
  level: reproduced (reproduction)
  record: .veriphy/runs/reproduce/39da61d5….json
```

The output says what the step ran on, the result in words, why (an error, a comparison, a counterexample), the level it
granted, and where the record is. The exit status is 0 when the step accepted, 1 when it refused or found a
counterexample, 2 on bad usage, and 3 when the result is unchecked or undecided. `--json` prints the record itself,
for scripts and agents.

A record's name is the digest of the content of the step's inputs, not their paths. Running a step again on the same
content returns the record it has, without running anything:

```console
$ veriphy layers step reproduce analysis.py survey.csv --claimed 0.127 --claim trust-education
reproduce analysis.py: agrees
  …
  record: .veriphy/runs/reproduce/39da61d5….json, replayed: its inputs did not change
```

Change the data, the script or the configuration, and the step runs again. `--rerun` runs it anyway, and keeps both
records when the result changed. A record whose result is `unchecked` or `failed` describes the machine rather than the
inputs, so the step runs again next time. Records live in `.veriphy/runs/`, out of git: deleting them only means the
steps run again.

`veriphy layers step list` shows the workspace's steps, with the pack each comes from, and `veriphy layers step
records` lists the records. In Python, `veriphy.run('reproduce', 'analysis.py', data='survey.csv', claimed=0.127)`
runs the same step and returns its result.

### Kinds of step

| Kind | Does | Example |
|---|---|---|
| check | accepts or refuses, and may grant a level | `check`, `reproduce`, `recompute` |
| evidence | reports something about the inputs, granting no level | `sample`, `check-concepts`, `validate` |
| derived | computed from other results | `levels`, `appendix` |
| agent | records a file an agent wrote, with its author | `record-statement`, `record-proof`, `record-claims` |

An agent step records what an agent wrote so that a workflow can tell it was written, and when:

```console
$ veriphy layers step record-statement Claim.lean --by alice
record-statement Claim.lean: recorded
  written by alice
```

## Levels and trust

A level says how far a claim is verified, and its trust class says by what kind of evidence:

| Trust class | Evidence | Example levels |
|---|---|---|
| `kernel` | a proof checked by a proof assistant's kernel | `lean-proof`, `certificate`, `kernel-test` |
| `checker` | a deterministic check by an independent checker | `dimensionally-consistent`, `sequence-checked`, `structure-checked` |
| `reproduction` | the same result recomputed from the same code and data | `recomputed`, `reproduced`, `robust`, `prediction-recomputed` |
| `oracle` | an evaluation by an untrusted system, exact or by intervals | `oracle-test`, `curvature-checked` |

Two more classes, `measurement` and `search`, describe tools that report or propose without establishing anything, so
they grant no level. Every report shows a level with its class, as `reproduced (reproduction)`, so a reproduction or an
oracle test never reads as a proof.

A step grants only a level of its tool's class: `veriphy config check` refuses a step that would do otherwise, and so
does the step when it writes its record. A step that compares its result with the claim grants its level only when the
comparison agrees.

The levels of a workspace form one order from `none`, which its packs build: each level names the level directly
below it. With the `math` pack, the order is `none`, `oracle-test`, `kernel-test`, `lean-proof`, `certificate`.
Combining packs is explained in [packs](../packs/index.md#combining-packs).

## Workflows

A workflow orders steps, and says what each result leads to. The `math` pack's `prove-claim`:

```yaml
workflows:
  prove-claim:
    - record-statement
    - sample: {counterexample: stop}
    - check: {refused: record-statement, attempts: 3}
    - record-proof
    - check: {refused: record-proof, attempts: 5}
```

`veriphy layers workflow next` reads the records whose inputs name the target, in the order they were written, and
names the next step with the command to type:

```console
$ veriphy layers workflow next prove-claim Claim.lean
prove-claim on Claim.lean: next is record-statement, an agent step: …
  write the file, then record it:
  veriphy layers step record-statement Claim.lean --by <your name>
```

`veriphy layers workflow run` runs every step that needs no agent, in order, and stops at the first that does. A step's
inputs are given as options: `veriphy layers workflow run prove-claim Claim.lean --declaration t`.

An entry can stop the workflow on a result (`{counterexample: stop}`), go back to an earlier step
(`{refused: record-statement}`), limit the attempts (`attempts: 3`, then `exhausted: stop` by default), or run only
while no record grants a level of some class (`when: {without: kernel}`). The same records always give the same next
step, so two agents working from them take the same path.

## The claim graph

Steps check one claim at a time. The claim graph checks how a source's claims fit together: which claims each rests
on, which conventions each assumes, and how verified each is once its weakest dependency counts. It is part of every
workspace.

### Sources

A source's claims live in `.veriphy/graph/sources/`, in Turtle, one file per provenance: `chapter3.agent.ttl` for
what an agent extracted, and `chapter3.human.ttl` for what a person wrote or confirmed. An agent never writes a
`.human.ttl` file.

```turtle
@prefix vp: <urn:veriphy:vocabulary#> .
@prefix : <urn:veriphy:source:chapter3#> .

:trust-index a vp:Convention ; vp:conventionFor "measure-of-social-trust" ;
    vp:statement "the mean of the three trust items" .
:trust-education a vp:Claim ; vp:statedIn :chapter3 ; vp:assumes :trust-index ;
    vp:statement "Each extra year of education raises social trust by 0.127 points." .
:policy a vp:Claim ; vp:statedIn :chapter3 ; vp:uses :trust-education ;
    vp:statement "Expanding schooling would raise social trust." .
```

A claim from another paper is a node of that paper's source, named by its DOI or arXiv identifier. `owl:sameAs` says
that two nodes mean the same thing. `veriphy layers claims vocabulary` prints every term.

```console
$ veriphy layers step validate                              # is the extraction complete?
validate: conforms
$ veriphy layers claims confirm chapter3 trust-education assumes trust-index   # a person confirms a triple
```

### Levels in the graph

A claim's own level is the highest level its records grant, when they name it (`--claim trust-education`), or the
level of the Lean declaration that formalizes it (`vp:formalizedBy`). Its effective level is the lowest level among
everything it uses, directly or not:

```console
$ veriphy layers claims levels --source chapter3
| claim | own | effective | capped by | Lean |
|---|---|---|---|---|
| policy | none | none |  |  |
| trust-education | robust (reproduction) | robust (reproduction) |  |  |
```

When a claim's effective level is lower than its own, the report names the claim that caps it.

### Reasoning, checked

`veriphy layers step reason` derives what the claims establish, and writes the derivation under
`.veriphy/graph/runs/`. The reasoner is untrusted: `oo-horn`, a verified Lean checker from
[Open Ontologies](https://github.com/fabio-rovai/open-ontologies) that shares no code with Veriphy, accepts or refuses
every run, and Veriphy reports a conclusion only with the checker's verdict:

| Verdict | Meaning |
|---|---|
| `entailed` | the checker accepted the run: every conclusion holds in every model of the assertions |
| `rejected` | the checker refused a derivation line, and names it |
| `unchecked` | no checker ran, and nothing is reported as checked |
| `incomplete` | the run stopped before it derived everything |

The first command that needs them sets up the reasoner and `oo-horn` from a pinned release, and caches them in
`~/.cache/veriphy/open-ontologies/`. On Linux x86_64 `oo-horn` is a prebuilt binary, checked against two hashes;
elsewhere it is built once with Lean, which takes minutes. `veriphy layers claims checker build` does it ahead of time.

`veriphy layers claims recheck .veriphy/graph/runs/<run>` checks a stored run again, and says whether the graph still
asserts the same thing.

### Conventions and clashes

Conventions for one aspect exclude each other. `veriphy layers claims excludes` proposes the exclusions, and
`--confirm` records them as a person's. `veriphy layers claims clashes` then reports every claim that rests on two
conventions that exclude each other, including assumptions inherited through the claims it cites:

```console
$ veriphy layers claims clashes
1 clashes (run e4546f587119: entailed):
- policy assumes trust-index and trust-single-item
```

`veriphy layers claims impact chapter3 trust-index` lists every claim that rests on a convention. Before changing one,
`veriphy layers claims plan --against HEAD` shows what the change does to the claims: the assumptions, the level caps
and the clashes it adds or removes.

### Slices and the appendix

`veriphy layers claims slice chapter3 policy` prints what an agent needs to work on one claim: its statement, the
claims it uses with their levels, and the conventions it assumes. `veriphy layers step appendix chapter3 --format
latex` writes the verification appendix for the paper: each claim with its levels, what caps it and its clashes, and
the command that rechecks the run.

### What the graph can't tell you

- Whether a prose claim and its formal statement say the same thing: `formalizedBy` is an assertion, and reports
  count who made it.
- Whether the extraction is right: a wrong extraction gives a faithfully wrong conclusion.
- That there is no clash: finding none is the reasoner's result, not a checked conclusion.

## Agents and skills

A pack's playbooks tell an agent how to do the field's work: which steps to run, what to write, and when to stop.
`veriphy layers agents path` prints where they are (`--pack statistics` for that pack's), and `veriphy layers
agents list` names every playbook, recipe and template. Any agent can follow them.

In Claude Code, each skill follows a workflow. It asks `veriphy layers workflow next` for the step, writes what is
asked when the step is the agent's, records it, and lets `veriphy layers workflow run` do the rest.

| Skill | Pack | Workflow |
|---|---|---|
| `prove` | `math` | `prove-claim` |
| `certify` | `math` | one goal, inside `prove` |
| `research` | `math` | `verify-paper` |
| `reproduce` | `statistics` | `reproduce-analysis` |

## The layers

![The layers](../architecture/diagrams/layers.svg)

Underneath, Veriphy is built in five layers, each using only the ones below, and each with its own commands under
`veriphy layers`: primitives (0), single operations, recording nothing; steps (1); claims (2); workflows (3); and
agents (4). A pack can add to each layer. The [architecture](../architecture/index.md) explains the design.
