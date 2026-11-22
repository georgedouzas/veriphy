# The `social-science` pack

The `social-science` pack checks a study's claims the way a careful referee would. It reruns the authors' analysis
from their own Python script and data, tests whether each estimate survives variations declared in advance,
recomputes the reliability of its scales with pingouin, and checks that the constructs the claims talk about (social
trust, educational attainment) are concepts of a recognised thesaurus. It builds on [`statistics`](statistics.md),
whose steps it brings, and needs neither Lean nor SageMath.

```console
$ pip install 'veriphy[social-science]'
```

```yaml
# veriphy.yaml
version: 1
packs: [social-science]
```

## A first session

The example study, in
[`docs/examples/social-science/`](https://github.com/georgedouzas/veriphy/tree/main/docs/examples/social-science),
asks whether education raises social trust, on a survey of 200 respondents. The data is synthetic, made for the
example. Its files:

| File | Holds |
|---|---|
| `survey.csv` | the data: education, age, income, three trust items and their mean, `trust_index` |
| `analysis.py` | the authors' analysis: `run(data, inputs)`, an ordinary least squares regression |
| `thesaurus.ttl` | an excerpt of a social-science thesaurus, in SKOS, in the shape of ELSST |
| `chapter3.agent.ttl` | the chapter's claims, its constructs and how each claim measures them |

The chapter reports that each extra year of education raises social trust by 0.127 points. Reproduce it from the
published script and data, naming the data's digest so that no other data is used:

```console
$ veriphy layers step reproduce analysis.py survey.csv --sha256 9eeed72a… --claimed 0.127 --claim trust-education
reproduce analysis.py: agrees
  found 0.1265132608543874, the claim says 0.127 (tolerance 0.0005)
  level: reproduced (reproduction)
  record: .veriphy/runs/reproduce/39da61d5….json
```

The paper reports a rounded figure, so the estimate agrees when it rounds to it: the tolerance is half a unit in the
last digit reported. Then test the variations the study declares, decided before seeing any result:

```console
$ veriphy layers step robustness analysis.py survey.csv \
    --variation "trust_index ~ education_years + age" \
    --variation "trust_index ~ education_years + income" --claim trust-education
robustness analysis.py: robust under every variation
  level: robust (reproduction)
```

`robust` means the estimate keeps its sign and stays significant at 5% under every variation. Otherwise the result is
`fragile`, and the record names the variations that break it.

## Scales

The trust index is the mean of three items. The chapter reports its reliability, Cronbach's alpha, as .76:

```console
$ veriphy layers step check-reliability survey.csv --item trust_q1 --item trust_q2 --item trust_q3 --claimed 0.76
check-reliability survey.csv: agrees
  found 0.75618, the claim says 0.76 (tolerance 0.005)
```

Reliability is evidence about the measure, not about a claim, so it grants no level.

## Constructs and the thesaurus

A claim in the social sciences is about constructs, and two studies can mean different things by the same word. In the
claim graph, a construct is a `vp:Concept`, linked by `owl:sameAs` to a concept of a thesaurus:

```turtle
:social-trust a vp:Concept ; owl:sameAs <https://example.org/thesaurus/social-trust> .
```

`check-concepts`, which every workspace has, checks that every construct names a concept the thesaurus defines, and reports the thesaurus's label
for each:

```console
$ veriphy layers step check-concepts thesaurus.ttl
check-concepts thesaurus.ttl: conforms
  concepts: education is "educational attainment"; social-trust is "social trust"
```

The thesaurus is any SKOS file: an excerpt of [ELSST](https://elsst.cessda.eu), the thesaurus of the European social
science data archives, or a project's own. The check is evidence about definitions, not about any claim, so it grants no
level.

## Measures as conventions

How a construct is measured is a choice, and the pack treats it as a convention. In the example, one claim measures
social trust by the mean of three items, another by the first item alone, and a policy claim rests on both:

```turtle
:trust-index a vp:Convention ; vp:conventionFor "measure-of-social-trust" ;
    vp:statement "the mean of the three trust items, trust_q1 to trust_q3" .
:trust-single-item a vp:Convention ; vp:conventionFor "measure-of-social-trust" ;
    vp:statement "the first trust item, trust_q1, alone" .
```

Conventions for the same aspect exclude each other. Confirm that, and the claim graph finds the claim that rests on
both:

```console
$ veriphy layers claims excludes --confirm
trust-index excludes trust-single-item
wrote 1 triples as human assertions
$ veriphy layers step reason
reason: entailed: oo-horn accepted the derivation
$ veriphy layers claims clashes
1 clashes (run e4546f587119: entailed):
- policy assumes trust-index and trust-single-item
```

The pack also declares two aspects of its own: `identification` (`parallel-trends`, `no-parallel-trends`) and
`sampling` (`probability-sample`, `convenience-sample`).

## Levels in the claim graph

`--claim` ties a record to a claim of the graph, which gives the claim the record's level:

```console
$ veriphy layers claims levels --source chapter3
| claim | own | effective | capped by | Lean |
|---|---|---|---|---|
| policy | none | none |  |  |
| trust-education | robust (reproduction) | robust (reproduction) |  |  |
| trust-item | none | none |  |  |
```

Both levels are of the `reproduction` trust class, so every report shows `robust (reproduction)`, never a proof.

## Steps, levels and workflow

| Step | Kind | Does | Grants |
|---|---|---|---|
| `reproduce <script> <data> [--sha256 d] [--claimed v] [--claim c]` | check | runs the script on the data in a fresh Python process, and compares its estimate with the claim | `reproduced` |
| `robustness <script> <data> --variation v … [--sha256 d] [--claim c]` | check | reruns it under each declared variation | `robust` |
| `check-reliability <data> --item c … [--claimed a]` | evidence | recomputes a scale's Cronbach's alpha | |
| `check-concepts <thesaurus>` | evidence | checks every construct against the thesaurus | |

`reproduce` and `robustness` come from [`statistics`](statistics.md), which describes the script's contract: the
example's `analysis.py` fits its model with statsmodels.

The workflow `check-study` runs `record-claims`, `check-concepts`, `reproduce` and `robustness` in turn, and the
`reproduce` skill follows it, with the playbook that `veriphy layers agents path --pack statistics` shows.
