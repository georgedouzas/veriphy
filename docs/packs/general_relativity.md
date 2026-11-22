# The `general-relativity` pack

The `general-relativity` pack checks what a text claims of a metric: that it solves the vacuum Einstein equations,
that it is flat, or that its Ricci scalar is a given expression. [EinsteinPy](https://einsteinpy.org) computes the
curvature, and SymPy simplifies what must vanish. It builds on [`physics`](physics.md).

```console
$ pip install 'veriphy[general-relativity]'
```

```yaml
# veriphy.yaml
version: 1
packs: [general-relativity]
```

## Metrics

```console
$ veriphy layers step check-metric "t r theta phi" \
    "diag(-(1 - 2*M/r), 1/(1 - 2*M/r), r**2, r**2*sin(theta)**2)" vacuum --claim schwarzschild
check-metric t r theta phi: accepted
  level: curvature-checked (oracle)
  record: .veriphy/runs/check-metric/….json
$ veriphy layers step check-metric "t r theta phi" \
    "diag(-(1 - 2*M/r**2), 1/(1 - 2*M/r**2), r**2, r**2*sin(theta)**2)" vacuum
check-metric t r theta phi: refused
  why: 2*M*(2*M - r**2)/r**6 is not zero: at {'M': 6.666666666666667, 'r': 21.333333333333332}
  record: .veriphy/runs/check-metric/….json
$ veriphy layers step check-metric "t x y z" "diag(-1, exp(2*H*t), exp(2*H*t), exp(2*H*t))" "R = 12*H**2"
check-metric t x y z: accepted
  level: curvature-checked (oracle)
  record: .veriphy/runs/check-metric/….json
```

The metric is a SymPy matrix, `diag(...)` or a nested list, over the coordinates; every other name is a constant.
The property is `vacuum` (the Ricci tensor vanishes), `flat` (the Riemann tensor vanishes) or `R = <expression>`.

When SymPy cannot reduce a residual to zero, the check evaluates it at points: a value away from zero refuses the
claim, with the point, and values that all vanish leave it `undecided`, which grants nothing. The level is of the
`oracle` class, as a computer algebra system's answer is; a proof in Lean, with the [`math`](math.md) pack, is
stronger.

## Steps, levels and conventions

| Step | Kind | Does | Grants |
|---|---|---|---|
| `check-metric <coordinates> <metric> <property>` | check | checks the curvature a claim gives a metric | `curvature-checked` |

`curvature-checked` sits above `dimensionally-consistent`. The convention `riemann-sign` (`mtw-riemann-sign`,
`opposite-riemann-sign`) adds to the `physics` pack's `metric-signature`: the sign of a Ricci scalar depends on both.
