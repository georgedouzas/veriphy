# The `economics` pack

The `economics` pack recomputes the statistics a paper's tables report from its published data, with pandas: a mean,
median or sum of a column, or its growth over the rows. It builds on [`statistics`](statistics.md), whose steps come
with it. For regressions, use [`econometrics`](econometrics.md), which builds on this pack.

```console
$ pip install 'veriphy[economics]'
```

```yaml
# veriphy.yaml
version: 1
packs: [economics]
```

## A first session

The example, in
[`docs/examples/economics/`](https://github.com/georgedouzas/veriphy/tree/main/docs/examples/economics), is a
synthetic table of real GDP and inflation from 2015 to 2024. A paper says real GDP grew by 1.6% a year:

```console
$ veriphy layers step recompute gdp.csv real_gdp cagr --claimed 0.016 --claim gdp-growth
recompute gdp.csv: agrees
  found 0.0159639, the claim says 0.016 (tolerance 0.0005)
  level: recomputed (reproduction)
  record: .veriphy/runs/recompute/….json
```

The statistic is `mean`, `median`, `sum`, `growth` (from the first row to the last, as a fraction) or `cagr`, the
compound annual growth rate over the rows less one, or over `--periods`.

## Steps, levels and workflow

| Step | Kind | Does | Grants |
|---|---|---|---|
| `recompute <data> <column> <statistic> [--claimed v] [--periods n]` | check | recomputes a statistic of a column, and compares it with the claim | `recomputed` |

and the `statistics` steps. The conventions are `price-basis` (`nominal-prices`, `real-prices`) and
`seasonal-adjustment` (`seasonally-adjusted`, `not-seasonally-adjusted`): a claim resting on figures in both nominal
and real prices is a clash in the claim graph. The workflow `check-table` runs `record-claims` and `recompute`.
Concepts can be checked against a classification, such as JEL, with `check-concepts`.
