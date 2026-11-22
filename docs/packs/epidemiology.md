# The `epidemiology` pack

The `epidemiology` pack recomputes survival analyses with [lifelines](https://lifelines.readthedocs.io): a Cox
model's hazard ratio and a Kaplan-Meier median survival time. It builds on [`statistics`](statistics.md).

```console
$ pip install 'veriphy[epidemiology]'
```

```yaml
# veriphy.yaml
version: 1
packs: [epidemiology]
```

## A first session

The example, in
[`docs/examples/epidemiology/`](https://github.com/georgedouzas/veriphy/tree/main/docs/examples/epidemiology), is a
synthetic trial of 240 patients followed for up to 36 months. The paper reports a hazard ratio of 0.63 for treatment,
adjusted for age, and median survival of 19.2 months in the control arm:

```console
$ veriphy layers step check-hazard-ratio trial.csv months died --covariate treated --covariate age \
    --claimed 0.63 --claim treatment-hr
check-hazard-ratio trial.csv: agrees
  found 0.625649, the claim says 0.63 (tolerance 0.005)
  level: recomputed (reproduction)
$ veriphy layers step check-median-survival trial.csv months died --group arm=control --claimed 19.2
check-median-survival trial.csv: agrees
  found 19.2, the claim says 19.2 (tolerance 0.05)
  level: recomputed (reproduction)
$ veriphy layers step check-median-survival trial.csv months died --group arm=treatment --claimed 30
check-median-survival trial.csv: differs from the claim
  found 32.5, the claim says 30 (tolerance 0.5)
```

The data has a row per subject: the time to the event or to censoring, and whether the event happened. The hazard
ratio is the first covariate's; the record keeps its 95% interval and the subjects and events counted. A median that
is not reached, because fewer than half had the event, fails rather than being guessed.

## Steps, levels and conventions

| Step | Kind | Does | Grants |
|---|---|---|---|
| `check-hazard-ratio <data> <duration> <event> --covariate c … [--claimed v]` | check | refits a Cox model | `recomputed` |
| `check-median-survival <data> <duration> <event> [--group col=value] [--claimed v]` | check | recomputes a Kaplan-Meier median | `recomputed` |

and the `statistics` steps. The convention `analysis-population` (`intention-to-treat`, `per-protocol`) lets claims
say which population they analyse. The workflow `check-trial` runs `record-claims`, `check-hazard-ratio` and
`check-median-survival`.
