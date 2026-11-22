# The `statistics` pack

The `statistics` pack checks the numbers an empirical paper reports. It reruns the authors' analysis from their own
Python script and data, tests whether an estimate survives variations declared in advance, and checks that reported
statistics are consistent with each other: a p-value with its test statistic, a mean with its sample size. It uses
pandas, SciPy and statsmodels, and is the base of the `social-science`, `economics`, `econometrics` and `epidemiology`
packs.

```console
$ pip install 'veriphy[statistics]'
```

```yaml
# veriphy.yaml
version: 1
packs: [statistics]
```

## Reported statistics

A paper reports *t*(28) = 2.20, *p* = .036. `check-p-value` recomputes the p-value from the statistic with SciPy, at
the statistic as reported and at the ends of its rounding, as statcheck does:

```console
$ veriphy layers step check-p-value t 2.20 .036 --df 28 --claim effect
check-p-value t: agrees
  found 0.036225, the claim says 0.036 (tolerance 0.0005)
  record: .veriphy/runs/check-p-value/….json
$ veriphy layers step check-p-value t 2.20 .01 --df 28
check-p-value t: differs from the claim
  found 0.036225, the claim says 0.01 (tolerance 0.005)
  record: .veriphy/runs/check-p-value/….json
```

The test is `t`, `F` (with `--df 1,30`), `chi2`, `z` or `r`, and a bound such as `<.001` is accepted when it holds.
`check-mean` applies the GRIM test: a mean of integer answers must be a whole total divided by the sample size.

```console
$ veriphy layers step check-mean 5.19 28
check-mean 5.19: differs from the claim
  found [5.14, 5.18, 5.21], the claim says 5.19 (tolerance 0)
  record: .veriphy/runs/check-mean/….json
```

Both are evidence about a paper's reporting, not about its claims, so they grant no level.

## Reproducing an analysis

`reproduce` runs the authors' script on their data in a fresh Python process and compares its estimate with the
claim; `robustness` reruns it under each declared variation. The [`social-science`](social_science.md) page walks
through both on an example study.

The script defines `run(data, inputs)`. `data` is the CSV, read by `pandas.read_csv`. `inputs['variation']` is the
model to fit instead of the published one, empty for the published one. The script returns
`{'estimate': …, 'se': …}`. Python's and NumPy's random generators are seeded (`--seed`, 0 by default) before it runs.

## Steps, levels and workflow

| Step | Kind | Does | Grants |
|---|---|---|---|
| `reproduce <script> <data> [--sha256 d] [--claimed v]` | check | runs the script on the data, and compares its estimate with the claim | `reproduced` |
| `robustness <script> <data> --variation v …` | check | reruns it under each declared variation | `robust` |
| `check-p-value <test> <statistic> <claimed> [--df d] [--tails 1]` | evidence | recomputes a p-value from its statistic | |
| `check-mean <mean> <n> [--items k]` | evidence | applies the GRIM test | |

The levels are `recomputed` < `reproduced` < `robust`, all of the `reproduction` trust class. `recomputed` is
granted by the packs built on this one, when they recompute a single statistic from published data. The pack's
conventions are `identification` (`parallel-trends`, `no-parallel-trends`) and `sidedness` (`two-sided-test`,
`one-sided-test`). The workflow `reproduce-analysis` runs `record-claims`, `reproduce` and `robustness`, and the
`reproduce` skill follows it.
