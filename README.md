# Veriphy

Veriphy checks the claims in research papers, and keeps a record of every check.

A paper says "each extra year of education raises social trust by 0.127 points", or "this formula has consistent
units", or "this theorem holds". Veriphy runs the right check for each claim: the authors' own script on their data, a
units checker, or Lean for a proof. It records what it ran and what came out. Then it tells you how far each claim is
verified, and by what kind of evidence.

```console
$ veriphy layers step reproduce analysis.py survey.csv --claimed 0.127 --claim trust-education
reproduce analysis.py: agrees
  found 0.126513, the claim says 0.127 (tolerance 0.0005)
  level: reproduced (reproduction)
  record: .veriphy/runs/reproduce/3ac5….json
```

The authors' script gives 0.126513, which rounds to the 0.127 the paper reports. The claim's *level* is now
`reproduced`: the same number came out of the same code and data. That is weaker than a proof, and Veriphy never
presents it as one.

## What it checks

Checks are grouped by field, in *packs*. You choose the packs a project uses.

| Field | Checks | Uses |
|---|---|---|
| Mathematics | proofs, and whether a statement says what was meant | Lean, SageMath, PARI, GAP |
| Statistics | an analysis rerun from its script and data, its robustness, reported p-values and means | pandas, SciPy, statsmodels |
| Social science | the reliability of survey scales | pingouin |
| Economics | statistics of published tables, and regressions: OLS, IV, panel | pandas, linearmodels |
| Epidemiology | hazard ratios and median survival | lifelines |
| Physics | the units of a formula, physical constants, flavour predictions, curvature of a metric | pint, SciPy, flavio, EinsteinPy |
| Life sciences | sequences, ontology terms, variant calls and read depth | Biopython, pronto, pysam |
| Chemistry | molecules and reactions | RDKit |

Veriphy also checks how a paper's claims fit together. It finds the weakest claim under each conclusion, and the
conclusions that rest on incompatible assumptions.

## Install

```sh
pip install 'veriphy[statistics]'   # or the extra of another field; veriphy[all] installs every one
```

Mathematics needs SageMath and Lean: see [installation](https://georgedouzas.github.io/veriphy/overview/install/).

## Learn more

- [Getting started](https://georgedouzas.github.io/veriphy/overview/getting_started/): a ten-minute tour
- [Tutorial](https://georgedouzas.github.io/veriphy/overview/tutorial/): every command on one example study
- [User guide](https://georgedouzas.github.io/veriphy/overview/user_guide/): how checks, records, levels, workflows and
  the claim graph work
- [Packs](https://georgedouzas.github.io/veriphy/packs/): each field's checks, and how to write your own
- [Commands](https://georgedouzas.github.io/veriphy/overview/commands/): every command and option
