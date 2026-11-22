# Proposal

## Why

Veriphy shipped one pack for an empirical field, `social-science`, and its checks were written by hand. A pack should
check claims the way its field already does, with the field's standard libraries, so that a check means what the field
takes it to mean. Fields are also too broad to share one set of checks: a particle physicist trusts flavio, a
relativist EinsteinPy, an epidemiologist lifelines.

## What Changes

- New field packs, each built on its field's standard libraries and installed with its extra:
  `statistics` (pandas, SciPy, statsmodels), `economics` (pandas), `physics` (pint, SciPy's CODATA), `life-sciences`
  (Biopython, pronto) and `chemistry` (RDKit).
- New subfield packs, each requiring the field pack it builds on: `particle-physics` (flavio, wilson, particle) and
  `general-relativity` (EinsteinPy) over `physics`, `genomics` (pysam) over `life-sciences`, `econometrics`
  (linearmodels) over `economics`, and `epidemiology` (lifelines) over `statistics`.
- **BREAKING** `reproduce`, `robustness`, the analysis runner, the `reproduce` playbook and skill, and the levels
  `reproduced` and `robust` move from `social-science` to `statistics`, which `social-science` now requires. The
  analysis script receives its data as a pandas DataFrame. `social-science` adds `check-reliability` (pingouin) and
  the workflow `check-study`.
- **BREAKING** `check-concepts` belongs to the framework pack, so every workspace has it, and reads OBO and OWL
  ontologies with pronto as well as SKOS thesauri.
- `statistics` declares `recomputed`, below `reproduced`, granted by the packs that recompute one statistic.
- A number a claim reports keeps its digits, so `tolerance: reported` is half a unit in the digit it was reported to,
  in scientific notation too; step output shows numbers to six significant digits.
- The example packs `economics` and `history` in `docs/examples/packs/` go, replaced by the shipped packs, whose
  examples are in `docs/examples/<pack>/`.

## Capabilities

### New Capabilities

- `packs/statistics`, `packs/economics`, `packs/physics`, `packs/life-sciences`, `packs/chemistry`: the field packs.
- `packs/particle-physics`, `packs/general-relativity`, `packs/genomics`, `packs/econometrics`,
  `packs/epidemiology`: the subfield packs.

### Modified Capabilities

- `packs/social-science`: requires `statistics`; reliability; the analysis, robustness and concepts move out.
- `core/steps`: reported numbers, and `check-concepts` in every workspace.
- `distribution/releases`: an extra per pack.

## Impact

The packs live in `src/veriphy/packs/<pack>/`, their examples in `docs/examples/`, their tests in `tests/packs/`. The
nox `tests` and `docs` sessions install `veriphy[all]`. PyR@TE, for beta functions, is not on PyPI, and `particle` is
held below 0.25, whose tables flavio 2.7 no longer finds.
