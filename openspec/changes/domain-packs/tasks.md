# Tasks

## 1. Field packs

- [x] 1.1 Add `statistics`, with the analysis runner, `reproduce`, `robustness`, `check-p-value` and `check-mean`
  (SciPy), and the levels `recomputed` < `reproduced` < `robust`; make `social-science` require it and add
  `check-reliability`.
- [x] 1.2 Add `economics`, `physics`, `life-sciences` and `chemistry`, each with its libraries, steps, levels and
  conventions; move `check-concepts` to the framework pack, reading OBO and OWL with pronto.
- [x] 1.3 Add an extra per pack and `all`, and install `all` in the nox `tests` and `docs` sessions.

## 2. Subfield packs

- [x] 2.1 Add `particle-physics` (flavio, wilson, particle) and `general-relativity` (EinsteinPy) over `physics`.
- [x] 2.2 Add `genomics` (pysam), `econometrics` (linearmodels) and `epidemiology` (lifelines).
- [x] 2.3 Keep a reported number's digits for `tolerance: reported`, and show numbers to six significant digits.

## 3. Docs and tests

- [x] 3.1 Write a page per pack, with its example, and the packs index, README, reference and architecture tables.
- [x] 3.2 Test every pack alone, with a correct and a wrong claim per step.

## 4. Gate

- [ ] 4.1 Run the gate and CI. Verify that every session and job is green.
