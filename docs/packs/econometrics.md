# The `econometrics` pack

The `econometrics` pack refits a paper's regressions from its published data with
[linearmodels](https://bashtage.github.io/linearmodels/): ordinary least squares, instrumental variables, or panel
models with entity and time effects. It builds on [`economics`](economics.md), and so on
[`statistics`](statistics.md).

```console
$ pip install 'veriphy[econometrics]'
```

```yaml
# veriphy.yaml
version: 1
packs: [econometrics]
```

## A first session

The example, in
[`docs/examples/econometrics/`](https://github.com/georgedouzas/veriphy/tree/main/docs/examples/econometrics), is a
synthetic panel of 50 firms over 8 years, in which firms that train more also pay more for reasons of their own. A
paper reports that an hour of training raises log wages by 0.080, with firm and year effects and errors clustered by
firm:

```console
$ veriphy layers step check-regression panel.csv "log_wage ~ training + EntityEffects + TimeEffects" training \
    --entity firm --time year --covariance clustered --claimed 0.080 --claim training-returns
check-regression panel.csv: agrees
  found 0.0800536, the claim says 0.08 (tolerance 0.0005)
  level: recomputed (reproduction)
```

Without the firm effects, the estimate absorbs the firms' differences:

```console
$ veriphy layers step check-regression panel.csv "log_wage ~ 1 + training" training --claimed 0.080
check-regression panel.csv: differs from the claim
  found 0.0945534, the claim says 0.08 (tolerance 0.0005)
```

The formula is in linearmodels' syntax. `y ~ 1 + x` is fitted by OLS, `y ~ 1 + x + [w ~ z]` by two-stage least
squares with `w` instrumented by `z`, and, with `--entity` and `--time`, `y ~ x + EntityEffects + TimeEffects` by
`PanelOLS`. The record names the estimator, the number of observations and the standard error.

## Steps, levels and conventions

| Step | Kind | Does | Grants |
|---|---|---|---|
| `check-regression <data> <formula> <coefficient> [--entity e --time t] [--covariance c] [--claimed v]` | check | refits a regression and compares a coefficient | `recomputed` |

and the `economics` and `statistics` steps. The conventions are `standard-errors` (`unadjusted-errors`,
`robust-errors`, `clustered-errors`) and `fixed-effects` (`entity-effects`, `time-effects`, `two-way-effects`). The
workflow `check-regressions` runs `record-claims` and `check-regression`.
