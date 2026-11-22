# The `physics` pack

The `physics` pack checks the formulas and constants a physics text uses. It checks that both sides of a formula have
the same dimensions, with pint, and compares a constant with its CODATA value, as SciPy ships it. It is the base of the
[`particle-physics`](particle_physics.md) and [`general-relativity`](general_relativity.md) packs, and combines with
[`math`](math.md) to prove a claim in Lean.

```console
$ pip install 'veriphy[physics]'
```

```yaml
# veriphy.yaml
version: 1
packs: [physics]
```

## Dimensions

`check-units` reads the formula as Python, gives each symbol its unit, and evaluates both sides:

```console
$ veriphy layers step check-units "E = m * c**2" --unit E=J --unit m=kg --unit c=m/s
check-units E = m * c**2: accepted
  level: dimensionally-consistent (checker)
  record: .veriphy/runs/check-units/….json
$ veriphy layers step check-units "T = 2 * pi * sqrt(L * g)" --unit T=s --unit L=m --unit "g=m/s**2"
check-units T = 2 * pi * sqrt(L * g): refused
  why: the left side is [time] and the right side [length] / [time]
  record: .veriphy/runs/check-units/….json
```

Units are in pint's notation. `pi` is a number, the arguments of `exp`, `log`, `sin` and the other elementary
functions must be dimensionless, and a symbol without a unit is named.

## Constants

```console
$ veriphy layers step check-constant "Newtonian constant of gravitation" --claimed 6.674e-11
check-constant Newtonian constant of gravitation: agrees
  found 6.6743e-11, the claim says 6.674e-11 (tolerance 5e-15)
  record: .veriphy/runs/check-constant/….json
```

The value is in CODATA's unit. The record names SciPy's version, and so the CODATA release.

## Steps, levels and conventions

| Step | Kind | Does | Grants |
|---|---|---|---|
| `check-units <formula> --unit s=u …` | check | checks that both sides have the same dimensions | `dimensionally-consistent` |
| `check-constant <name> [--claimed v]` | evidence | compares a constant with CODATA | |

The conventions are `metric-signature` (`mostly-plus`, `mostly-minus`), `unit-system` (`si-units`, `natural-units`,
`gaussian-units`) and `fourier-sign` (`fourier-minus-i`, `fourier-plus-i`).
