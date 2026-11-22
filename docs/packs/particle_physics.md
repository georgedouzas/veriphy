# The `particle-physics` pack

The `particle-physics` pack checks the numbers of flavour physics with the field's own codes. It recomputes an
observable's prediction with [flavio](https://flav-io.github.io), in the Standard Model or with new-physics Wilson
coefficients, runs coefficients between scales with [wilson](https://wilson-eft.github.io), and reads particle
properties from the PDG tables that the `particle` package ships. It builds on [`physics`](physics.md).

```console
$ pip install 'veriphy[particle-physics]'
```

```yaml
# veriphy.yaml
version: 1
packs: [particle-physics]
```

## Predictions

A paper quotes the Standard Model prediction BR(B<sub>s</sub> → μμ) = (3.66 ± 0.14) × 10<sup>-9</sup>:

```console
$ veriphy layers step check-prediction "BR(Bs->mumu)" 3.66e-9 --uncertainty 0.14e-9 --claim bs-mumu-sm
check-prediction BR(Bs->mumu): agrees
  found 3.62893e-09, the claim says 3.66e-09 (tolerance 3.53738e-10)
  level: prediction-recomputed (reproduction)
  record: .veriphy/runs/check-prediction/….json
$ veriphy layers step check-prediction "BR(Bs->mumu)" 2.9e-9 --uncertainty 0.1e-9
check-prediction BR(Bs->mumu): differs from the claim
  found 3.62893e-09, the claim says 2.9e-09 (tolerance 3.38476e-10)
  record: .veriphy/runs/check-prediction/….json
```

The claim agrees when it is within two combined uncertainties (`--sigmas`) of flavio's prediction: flavio's theory
uncertainty, from a seeded Monte Carlo over its parameters, combined with the claim's. With new physics, give the
coefficients at their scale:

```console
$ veriphy layers step check-prediction "BR(Bs->mumu)" 5.6e-9 --coefficient C10_bsmumu=-1
check-prediction BR(Bs->mumu): agrees
  found 5.57993e-09, the claim says 5.6e-09 (tolerance 3.56672e-10)
  level: prediction-recomputed (reproduction)
  record: .veriphy/runs/check-prediction/….json
```

The observable is flavio's name for it; `--arguments 1.1,6` gives a q² bin.

## Running coefficients

A SMEFT operator at 1 TeV induces C<sub>9</sub> at the b-quark scale. `run-coefficients` runs it with wilson,
matching onto the weak effective theory:

```console
$ veriphy layers step run-coefficients C9_bsmumu 4.8 --coefficient lq1_2223=1e-8 --to-eft WET --to-basis flavio --claimed -5.66
run-coefficients C9_bsmumu: agrees
  found -5.65788, the claim says -5.66 (tolerance 0.005)
  level: prediction-recomputed (reproduction)
  record: .veriphy/runs/run-coefficients/….json
```

The starting point is SMEFT in the Warsaw basis at 1000 GeV unless `--scale`, `--eft` and `--basis` say otherwise.

## PDG values

```console
$ veriphy layers step check-pdg "B(s)0" mass 5366.9
check-pdg B(s)0: agrees
  found 5366.92, the claim says 5366.9 (tolerance 0.25)
  record: .veriphy/runs/check-pdg/….json
$ veriphy layers step check-pdg "B(s)0" mass 5279.3
check-pdg B(s)0: differs from the claim
  found 5366.92, the claim says 5279.3 (tolerance 0.25)
  record: .veriphy/runs/check-pdg/….json
```

Masses and widths are in MeV, lifetimes in ns; a particle is named as the PDG names it, or by its Monte Carlo number.

## Steps, levels and conventions

| Step | Kind | Does | Grants |
|---|---|---|---|
| `check-prediction <observable> <claimed> [--uncertainty u] [--coefficient c=v …]` | check | recomputes a prediction with flavio | `prediction-recomputed` |
| `run-coefficients <coefficient> <to-scale> --coefficient c=v … [--claimed v]` | check | runs coefficients with wilson | `prediction-recomputed` |
| `check-pdg <particle> <property> <claimed>` | evidence | compares a mass, width or lifetime with the PDG's | |

`prediction-recomputed` is of the `reproduction` class, above `dimensionally-consistent`. The conventions are
`operator-basis` (`warsaw-basis`, `flavio-basis`, `jms-basis`) and `ckm-input` (`ckm-from-tree-level`,
`ckm-from-global-fit`). The workflow `check-flavour` runs `record-claims`, `check-pdg` and `check-prediction`.

The record names flavio's, wilson's and particle's versions: a prediction changes with flavio's inputs, so a
recorded agreement is an agreement with that version.
