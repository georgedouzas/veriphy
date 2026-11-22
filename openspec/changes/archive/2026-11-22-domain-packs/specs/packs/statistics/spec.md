## ADDED Requirements

### Requirement: Statistics pack
Veriphy SHALL ship a `statistics` pack, using pandas, SciPy and statsmodels, with the steps `reproduce`, `robustness`,
`check-p-value` and `check-mean`, the levels `recomputed` < `reproduced` < `robust` of the `reproduction` class, the
conventions `identification` and `sidedness`, the workflow `reproduce-analysis`, and the `reproduce` playbook and skill.

#### Scenario: Selecting the pack
- **WHEN** a workspace lists `packs: [statistics]`
- **THEN** `veriphy config check` passes, and the levels are `none` < `recomputed` < `reproduced` < `robust`

### Requirement: Analysis in Python
The pack SHALL run an analysis script, defining `run(data, inputs)`, in a fresh Python process, with the data as a
pandas DataFrame and `inputs['variation']`, Python's and NumPy's generators seeded before it runs, and SHALL record the
data's SHA-256. Data whose digest differs from a given `--sha256` SHALL be refused before the script runs.

#### Scenario: The example study
- **WHEN** `reproduce` runs the social-science example's `analysis.py` on `survey.csv`, claiming 0.127
- **THEN** it reproduces 0.1265, agrees within the reported tolerance, and grants `reproduced`

### Requirement: Robustness
`robustness` SHALL rerun the analysis under each declared variation, granting `robust` when the estimate keeps its sign
and its significance at 5% under every one, and recording `fragile` with the variations that break it otherwise.

#### Scenario: A variation that breaks it
- **WHEN** one declared variation makes the estimate insignificant
- **THEN** the status is `fragile`, the record names that variation, and no level is granted

### Requirement: Consistency of reported statistics
`check-p-value` SHALL recompute a p-value from a t, F, χ², z or r statistic with SciPy, at the statistic as reported and
at the ends of its rounding, and agree when the reported p-value, or bound, lies within that range. `check-mean` SHALL
apply the GRIM test. Both SHALL grant no level.

#### Scenario: A misreported p-value
- **WHEN** a source reports t(28) = 2.20, p = .01
- **THEN** the status is `differs`, with the recomputed p-value 0.036
