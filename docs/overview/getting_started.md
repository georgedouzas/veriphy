# Getting started

This page is a ten-minute tour of what Veriphy does. Each section shows one idea with one command and what it prints.
The [tutorial](tutorial.md) then uses every command on the same example, and the [user guide](user_guide.md)
explains the ideas in depth.

## Install

```sh
pip install 'veriphy[social-science]'
```

Veriphy groups its checks by field, in *packs*. Each pack's libraries come with an extra of the same name.
[Installation](install.md) lists them all, and explains how to set up mathematics with Lean.

## The example

A (fictitious) study claims that *each extra year of education raises social trust by 0.127 points*. Its authors
published their data, `survey.csv`, and their analysis script, `analysis.py`. Download the files of
[`docs/examples/social-science/`](https://github.com/georgedouzas/veriphy/tree/main/docs/examples/social-science) into
a new directory, and tell Veriphy which pack to use:

```console
$ printf 'version: 1\npacks: [social-science]\n' > veriphy.yaml
```

That file makes the directory a *workspace*: the place where Veriphy runs its checks and keeps its records.

## Check a number

Rerun the authors' analysis and compare its result with the claim:

```console
$ veriphy layers step reproduce analysis.py survey.csv --claimed 0.127 --claim trust-education
reproduce analysis.py: agrees
  found 0.126513, the claim says 0.127 (tolerance 0.0005)
  level: reproduced (reproduction)
  record: .veriphy/runs/reproduce/3ac5….json
```

The script gives 0.126513, which rounds to 0.127, so the claim agrees with the data. A check like this is called a
*step*.

A wrong number is refused, and the command exits with status 1:

```console
$ veriphy layers step reproduce analysis.py survey.csv --claimed 0.2
reproduce analysis.py: differs from the claim
  found 0.126513, the claim says 0.2 (tolerance 0.05)
  record: .veriphy/runs/reproduce/….json
```

## Every check is recorded

Each step writes a *record*: its inputs, the tools and their versions, and the result. Run the same check again and
Veriphy returns the record instead of recomputing:

```console
$ veriphy layers step reproduce analysis.py survey.csv --claimed 0.127 --claim trust-education
reproduce analysis.py: agrees
  found 0.126513, the claim says 0.127 (tolerance 0.0005)
  level: reproduced (reproduction)
  record: .veriphy/runs/reproduce/3ac5….json, replayed: its inputs did not change
$ veriphy layers step records
reproduce  agrees   3ac5…
reproduce  differs  d303…
```

If the script or the data change, the step runs again.

## Levels say how far a claim is verified

The first check gave the claim the *level* `reproduced`. The word in brackets, `reproduction`, names the kind of
evidence: the same number from the same code and data. Stronger checks give higher levels. `robustness` reruns the
analysis under variations the authors declared in advance:

```console
$ veriphy layers step robustness analysis.py survey.csv --claim trust-education --variation "trust_index ~ education_years + age"
robustness analysis.py: robust under every variation
  level: robust (reproduction)
  record: .veriphy/runs/robustness/….json
```

In mathematics, the levels go up to a proof checked by Lean. Every level is shown with its kind of evidence, so a
reproduced number never reads as a proof.

## Workflows say what to do next

A *workflow* is a list of steps in order. Veriphy reads the records and tells you, or an agent, which step is next:

```console
$ veriphy layers workflow next reproduce-analysis analysis.py
reproduce-analysis on analysis.py: next is record-claims, an agent step: record the file holding the claims an agent extracted from a source, with their author
  write the file, then record it:
  veriphy layers step record-claims analysis.py --by <your name>
```

## The claim graph checks how claims fit together

A paper's claims rest on each other. The *claim graph* holds them, finds the weakest link under each claim, and
reports claims that rest on incompatible assumptions. The example comes with the chapter's claims, as an agent
extracted them:

```console
$ mkdir -p .veriphy/graph/sources && mv chapter3.agent.ttl .veriphy/graph/sources/
$ veriphy layers claims excludes --confirm
trust-index excludes trust-single-item
wrote 1 triples as human assertions
$ veriphy layers step reason
reason: entailed: oo-horn accepted the derivation
  record: .veriphy/runs/reason/….json
$ veriphy layers claims clashes
1 clash (run …: entailed):
- policy assumes trust-index and trust-single-item
```

The chapter's policy claim rests on two claims that measure trust in two different ways, so Veriphy reports a clash.
The first command confirmed that the two measures exclude each other. `reason` worked out the consequences, and an
independent checker, `oo-horn`, accepted every step of that reasoning.

## Next steps

- The [tutorial](tutorial.md) uses every command on this example.
- The [user guide](user_guide.md) explains steps, records, levels, workflows, the claim graph and packs.
- The [packs](../packs/index.md) pages show the checks of each field: mathematics, statistics, physics, life sciences,
  chemistry and economics.
- The [command reference](commands.md) lists every command and option.
