## ADDED Requirements

### Requirement: An extra per pack
Each pack whose checks need libraries SHALL have an extra of its name that installs them, a subfield pack's including
its field pack's, and `veriphy[all]` SHALL install every one. A pack whose libraries are missing SHALL still load, its
primitives importing them only when they run.

#### Scenario: A subfield's extra
- **WHEN** `pip install 'veriphy[econometrics]'` runs
- **THEN** linearmodels, pandas, SciPy and statsmodels are installed
