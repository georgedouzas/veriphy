# Tutorial: every command on one study

This tutorial uses every Veriphy command once, on one small study. Each command is followed by what it prints. The test
suite runs this page, so the output you see is the output you get.

It takes about twenty minutes and needs Python 3.11 or later. Section 5 also needs the claim graph's checker. The
first command that uses it downloads it on Linux x86_64, and builds it with Lean elsewhere (see
[installation](install.md#the-claim-graphs-checker)).

## The study

A (fictitious) study asks whether education raises social trust. Chapter 3 makes three claims:

1. Each extra year of education raises social trust by 0.127 points.
2. On the first trust question alone, each year adds 0.117 points.
3. So expanding schooling would raise social trust.

The authors published their data and their analysis script. You want to know which of these claims hold up.

Install Veriphy with the libraries of the social sciences, then download the five files of
[`docs/examples/social-science/`](https://github.com/georgedouzas/veriphy/tree/main/docs/examples/social-science)
into a new directory:

```sh
pip install 'veriphy[social-science]'
```

| File | Holds |
|---|---|
| `survey.csv` | the data: 200 people, their education, age, income and answers to three trust questions |
| `analysis.py` | the authors' script: a regression of trust on education |
| `claim.json` | claim 1, written down: the number, the script, the data and its SHA-256, the variations to try |
| `chapter3.agent.ttl` | the three claims, as an agent extracted them from the chapter |
| `thesaurus.ttl` | an excerpt of a social-science thesaurus, naming the concepts the claims use |

## 1. Set up the workspace

A *workspace* is the directory Veriphy works in. Its `veriphy.yaml` names the *packs* it uses. A pack holds the checks
of one field. Here you need the `social-science` pack:

```console
$ printf 'version: 1\npacks: [social-science]\n' > veriphy.yaml
$ veriphy pack list
core            …/packs/core
statistics      …/packs/statistics
social-science  …/packs/social_science  statistics
```

`social-science` builds on `statistics`, so both are in use. `core` is always there: it holds the commands every field
shares.

`veriphy help` lists what you can run here:

```console
$ veriphy help
Layers (veriphy layers <layer> …):
  primitive          layer 0: list, describe or run a primitive, with no record
  step               layer 1: run a step and record it, list the steps and records
  claims             layer 2: the research claim graph: validate, reason, slice, …
  workflow           layer 3: the workflows, and a target's next steps
  agents             layer 4: the playbooks, recipes and templates agents follow

Steps (veriphy layers step <name> …, or veriphy.run(name, target, …) in Python):
  appendix           derived   write the verification appendix of a source: each claim with its level and what caps it
…
  validate           evidence  check that the extracted claims are complete, against the shapes
```

The commands come in five groups, from single operations up to agents. This tutorial goes through them in the order
you would use them: steps first.

`veriphy config check` checks that the packs fit together, and `veriphy config show` prints everything they declare:

```console
$ veriphy config check
config: 3 packs, no problems
$ veriphy config show
{
  "config": {
…
}
```

## 2. Check a claim

A *step* runs one check and keeps a record of it. `reproduce` runs the authors' script on their data and compares the
result with the number the claim reports:

```console
$ veriphy layers step reproduce analysis.py survey.csv --claimed 0.127 --claim trust-education
reproduce analysis.py: agrees
  found 0.126513, the claim says 0.127 (tolerance 0.0005)
  level: reproduced (reproduction)
  record: .veriphy/runs/reproduce/3ac5….json
```

The script finds 0.126513, which rounds to the reported 0.127, so the claim *agrees*. The claim now has the *level*
`reproduced`: the same number came out of the same code and data. The word in brackets, `reproduction`, is the kind of
evidence behind the level. A reproduced number is not a proof, and the output never lets it read as one.

Run it again and nothing is computed. The inputs haven't changed, so Veriphy returns the record it already has:

```console
$ veriphy layers step reproduce analysis.py survey.csv --claimed 0.127 --claim trust-education
reproduce analysis.py: agrees
  found 0.126513, the claim says 0.127 (tolerance 0.0005)
  level: reproduced (reproduction)
  record: .veriphy/runs/reproduce/3ac5….json, replayed: its inputs did not change
```

Change the script or the data and the step runs again. `--rerun` runs it anyway.

A number the analysis doesn't support is refused, and the command exits with status 1:

```console
$ veriphy layers step reproduce analysis.py survey.csv --claimed 0.2
reproduce analysis.py: differs from the claim
  found 0.126513, the claim says 0.2 (tolerance 0.05)
  record: .veriphy/runs/reproduce/….json
```

The tolerance comes from the claim's own digits: 0.2 means anything from 0.15 to 0.25.

### Is the estimate robust?

`claim.json` lists two variations of the model the authors declared in advance. `robustness` reruns the analysis with
each one, and checks that the estimate keeps its sign and stays significant:

```console
$ veriphy layers step robustness analysis.py survey.csv --claim trust-education --variation "trust_index ~ education_years + age" --variation "trust_index ~ education_years + income"
robustness analysis.py: robust under every variation
  level: robust (reproduction)
  record: .veriphy/runs/robustness/….json
```

`robust` is above `reproduced`, so claim 1 now stands at `robust`.

### Checks on reported statistics

Some checks need only the numbers a paper prints. The study reports a reliability (Cronbach's alpha) of 0.81 for its
three trust questions. `check-reliability` recomputes it from the data:

```console
$ veriphy layers step check-reliability survey.csv --item trust_q1 --item trust_q2 --item trust_q3 --claimed 0.81
check-reliability survey.csv: differs from the claim
  found 0.75618, the claim says 0.81 (tolerance 0.005)
  record: .veriphy/runs/check-reliability/….json
```

The data gives 0.756, not 0.81. The study reports *t*(28) = 2.20, *p* = .036, and a mean answer of 3.48 from 25
people. `check-p-value` recomputes the p-value from the test statistic, and `check-mean` checks that the mean is possible
for whole-number answers:

```console
$ veriphy layers step check-p-value t 2.20 .036 --df 28
check-p-value t: agrees
  found 0.036225, the claim says 0.036 (tolerance 0.0005)
  record: .veriphy/runs/check-p-value/….json
$ veriphy layers step check-mean 3.47 25
check-mean 3.47: differs from the claim
  found [3.44, 3.48, 3.52], the claim says 3.47 (tolerance 0)
  record: .veriphy/runs/check-mean/….json
```

No 25 whole numbers average 3.47: the nearest possible means are 3.44 and 3.48. These checks grant no level. They are
evidence about how a paper reports its numbers, not about its claims.

### Steps and records

`step list` shows every step of the workspace, with its kind and its pack:

```console
$ veriphy layers step list
appendix  derived  core  write the verification appendix of a source: each claim with its level and what caps it
…
validate  evidence  core  check that the extracted claims are complete, against the shapes
```

There are four kinds. A *check* accepts or refuses and can grant a level. An *evidence* step reports without granting
one. A *derived* step computes from other results. An *agent* step records a file an agent wrote.

`step records` lists the records, and shows one when you give the start of its name:

```console
$ veriphy layers step records
check-mean         differs  c841…
check-p-value      agrees   c846…
check-reliability  differs  5181…
reproduce          agrees   3ac5…
reproduce          differs  d303…
robustness         robust   ffc2…
$ veriphy layers step records 3ac5
{
  "config": "…",
  "digest": "3ac5…",
  "inputs": {
    "claim": "trust-education",
    "claimed": 0.127,
…
  "status": "agrees",
  "step": "reproduce",
  "tools": {
    "python": "…",
    "veriphy": "…"
  }
}
```

A record holds the inputs, the tools and their versions, the result and the level. Its name is a digest of the
inputs' contents, which is how Veriphy knows when to replay it. Records live in `.veriphy/runs/`. They can be deleted:
the steps then run again.

`--json` prints the record instead of the summary, for scripts and agents:

```console
$ veriphy layers step check-mean 3.48 25 --json
{
…
  "status": "agrees",
  "step": "check-mean",
…
}
```

## 3. Look underneath: primitives

Each step calls a *primitive*: one operation, run on a JSON input, that records nothing. You rarely need them, but
they show what a step does. `primitive list` names each, with its kind of evidence, its pack, and whether it can run
here:

```console
$ veriphy layers primitive list
analysis.exec  reproduction  statistics  available
…
stats.grim     reproduction  statistics  available
stats.p-value  reproduction  statistics  available
```

`primitive describe` shows a primitive's input and output, and `primitive run` runs it once:

```console
$ veriphy layers primitive describe stats.grim
{
  "name": "stats.grim",
  "pack": "statistics",
…
}
$ printf '{"mean": "3.48", "n": 25}' > grim.json
$ veriphy layers primitive run stats.grim --input grim.json
{
…
  "status": "agrees",
…
}
```

## 4. Follow a workflow

A *workflow* is an ordered list of steps. The workspace's records decide which step comes next, so you, or an agent,
can stop and resume at any time:

```console
$ veriphy layers workflow list
check-study         record-claims, check-concepts, reproduce, robustness
reproduce-analysis  record-claims, reproduce, robustness
```

Start `reproduce-analysis` on the script. Its first step belongs to an agent: write down the claims, then record who
wrote them.

```console
$ veriphy layers workflow next reproduce-analysis analysis.py
reproduce-analysis on analysis.py: next is record-claims, an agent step: record the file holding the claims an agent extracted from a source, with their author
  write the file, then record it:
  veriphy layers step record-claims analysis.py --by <your name>
$ veriphy layers step record-claims analysis.py --by alice
record-claims analysis.py: recorded
  written by alice
  record: .veriphy/runs/record-claims/….json
```

`record-statement` does the same for a statement an agent wrote, such as `claim.json`:

```console
$ veriphy layers step record-statement claim.json --by alice
record-statement claim.json: recorded
  written by alice
  record: .veriphy/runs/record-statement/….json
```

`workflow run` runs every following step that needs no agent, and stops at the end or at the next agent step:

```console
$ veriphy layers workflow run reproduce-analysis analysis.py --data survey.csv --claimed 0.127 --claim trust-education --variation "trust_index ~ education_years + age"
reproduce analysis.py: agrees
…
robustness analysis.py: robust under every variation
…
reproduce-analysis on analysis.py: done
```

The same records always give the same next step, so two agents working from them take the same path.

## 5. Check how the claims fit together

Steps check one claim at a time. Claim 3, "expanding schooling would raise social trust", rests on claims 1 and 2, and
they measure trust in two different ways. The *claim graph* finds problems like this.

The claims go in `.veriphy/graph/sources/`. A file whose name ends in `.agent.ttl` holds what an agent extracted, and
one ending in `.human.ttl` what a person confirmed. Open `chapter3.agent.ttl` to see the format. Move it into place,
and commit the workspace so you can compare changes later:

```console
$ mkdir -p .veriphy/graph/sources && mv chapter3.agent.ttl .veriphy/graph/sources/
$ git init -q && git add -A && git commit -qm "chapter 3 as extracted"
```

`validate` checks that the extraction is complete: every claim has a statement and a source. `check-concepts` checks
that each concept the claims use is in the field's thesaurus:

```console
$ veriphy layers step validate
validate: conforms
  record: .veriphy/runs/validate/….json
$ veriphy layers step check-concepts thesaurus.ttl
check-concepts thesaurus.ttl: conforms
  concepts: education is "educational attainment"; social-trust is "social trust"
  record: .veriphy/runs/check-concepts/….json
```

A *convention* is a choice a claim assumes, here how trust is measured. Claim 1 uses the mean of three questions
(`trust-index`), and claim 2 the first question alone (`trust-single-item`). Two conventions for the same thing
exclude each other. `claims excludes` proposes those exclusions, and `--confirm` records them as yours:

```console
$ veriphy layers claims excludes
trust-index excludes trust-single-item
$ veriphy layers claims excludes --confirm
trust-index excludes trust-single-item
wrote 1 triples as human assertions
```

`reason` works out what follows from the claims. A separate checker, `oo-horn`, written and proved correct in Lean
by another project, checks every derivation:

```console
$ veriphy layers step reason
reason: entailed: oo-horn accepted the derivation
  record: .veriphy/runs/reason/….json
```

Now the graph can answer questions. `clashes` finds claims that rest on two conventions that exclude each other:

```console
$ veriphy layers claims clashes
1 clash (run …: entailed):
- policy assumes trust-index and trust-single-item
```

Claim 3 (`policy`) mixes the two measures of trust. `levels` shows how far each claim is verified. A claim's *own*
level comes from its records. Its *effective* level is the lowest among everything it rests on:

```console
$ veriphy layers claims levels --source chapter3
Run …: entailed

| claim | own | effective | capped by | Lean |
|---|---|---|---|---|
| policy | none | none |  |  |
| trust-education | robust (reproduction) | robust (reproduction) |  |  |
| trust-item | none | none |  |  |

robust: 1, reproduced: 0, recomputed: 0, none: 2
```

`impact` lists the claims that depend on a convention, and `slice` prints everything an agent needs to work on one
claim:

```console
$ veriphy layers claims impact chapter3 trust-index
Impact of trust-index (run …: entailed)

## chapter3

- policy via trust-education
- trust-education
$ veriphy layers claims slice chapter3 policy
# Context for policy

Expanding schooling would raise social trust.

## Uses

- trust-education [robust]: Each extra year of education raises social trust by 0.127 points.
- trust-item [none]: On the first trust item alone, each year of education adds 0.117 points.
…
Level: own none, effective none (checked)
```

`confirm` moves one statement from the agent's file to the human file, once you have checked it against the chapter.
`plan` then shows what your edits since the last commit change:

```console
$ veriphy layers claims confirm chapter3 trust-education assumes trust-index
confirmed in …/.veriphy/graph/sources/chapter3.human.ttl
$ veriphy layers claims plan --against HEAD
2 changed assertions
+ trust-education hasLevel robust
+ trust-index excludes trust-single-item

4 changed consequences (checked)
+ policy excludes trust-single-item
- trust-education cappedAt none
- trust-education cappedAt recomputed
- trust-education cappedAt reproduced
```

Since the commit, claim 1 gained the level `robust` and you confirmed the exclusion. As a result, `policy` now has a
clash, and claim 1 is no longer held down at the lower levels.

`recheck` runs the checker again on a stored run, and says whether the graph still says the same:

```console
$ veriphy layers claims recheck .veriphy/graph/runs/$(ls .veriphy/graph/runs | grep -v slices | head -1)
run: .veriphy/graph/runs/…
asserted: 84, derived: 59, complete: True
status: accepted, verdict: entailed (OOCert.entails_of_builtin_horn)
the current graph asserts the same triples
```

`appendix` writes it all up as an appendix for the paper, in Markdown or LaTeX:

```console
$ veriphy layers step appendix chapter3
appendix chapter3: recorded
  wrote .veriphy/graph/appendix/chapter3.md
  record: .veriphy/runs/appendix/….json
```

The graph is written in RDF. `vocabulary` prints the terms a source file can use, and `axioms` the rules the reasoner
derives from the workspace's conventions and levels:

```console
$ veriphy layers claims vocabulary
@prefix vp: <urn:veriphy:vocabulary#> .
…
$ veriphy layers claims axioms
…
```

`checker path` says where the checker is. `checker build` fetches or builds it ahead of time, which the first
`reason` otherwise does for you:

```console
$ veriphy layers claims checker path
…/oo-horn
$ veriphy layers claims checker build
Open Ontologies v2.1.0 (…)
reasoner: …
checker: …/oo-horn
```

## 6. Hand the work to an agent

A pack ships *playbooks*: instructions an agent follows to do the field's work. `agents path` says where a pack's are,
`agents list` names them, and `agents show` prints one:

```console
$ veriphy layers agents path --pack statistics
…/packs/statistics/agents
$ veriphy layers agents list --pack statistics
reproduce.md
skills/reproduce/SKILL.md
$ veriphy layers agents show reproduce --pack statistics
# Reproduce an analysis
…
```

In Claude Code, the `/veriphy:reproduce` skill follows this playbook: it runs `workflow next`, does the agent's steps,
and lets `workflow run` do the rest. `agents copy` copies a template into the workspace. Only the `math` pack has
templates, so it appears on the [math page](../packs/math.md).

## 7. From Python

Every step can be run from Python, with the same records:

```console
$ python -c "import veriphy; print(veriphy.run('check-mean', '3.48', n=25).status)"
agrees
```

## What you used

| Group | Commands |
|---|---|
| workspace | `help`, `pack list`, `config check`, `config show` |
| steps | `step <name>`, `step list`, `step records` |
| primitives | `primitive list`, `primitive describe`, `primitive run` |
| workflows | `workflow list`, `workflow next`, `workflow run` |
| claim graph | `validate`, `check-concepts`, `reason`, `appendix`, and `claims excludes`, `clashes`, `levels`, `impact`, `slice`, `confirm`, `plan`, `recheck`, `vocabulary`, `axioms`, `checker` |
| agents | `agents path`, `agents list`, `agents show` |

The [user guide](user_guide.md) explains each idea in more depth, and the [command reference](commands.md) lists
every option.
