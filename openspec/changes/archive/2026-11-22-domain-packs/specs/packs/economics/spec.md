## ADDED Requirements

### Requirement: Economics pack
Veriphy SHALL ship an `economics` pack, requiring `statistics`, whose step `recompute` recomputes a column's mean,
median, sum, growth or compound annual growth rate with pandas and compares it with the claim within the reported
tolerance, granting `recomputed`, with the conventions `price-basis` and `seasonal-adjustment`.

#### Scenario: A growth rate
- **WHEN** `recompute gdp.csv real_gdp cagr --claimed 0.016` runs on the example
- **THEN** it agrees and grants `recomputed`, and a claim of 0.025 differs and grants nothing
