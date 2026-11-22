## MODIFIED Requirements

### Requirement: Meaning check
`#veriphy sample c [seed s] [values n] [points p]` and `veriphy layers step sample <file> <declaration>` SHALL evaluate
the statement of `c` at seeded values satisfying its hypotheses and domain conditions, or at given points, exactly or by
intervals of at least 53 bits, and report `agrees`, `counterexample` or `undecided`. The step SHALL be of kind
`evidence` and SHALL grant no level.

#### Scenario: A wrong formalization
- **WHEN** the claim `∀ x : ℝ, 0 ≤ x → Real.sqrt (x ^ 2) = -x` is sampled
- **THEN** the outcome is `counterexample`, with a value of `x` and both sides

#### Scenario: A faithful formalization
- **WHEN** the claim `∀ x : ℝ, Real.sqrt (x ^ 2) = |x|` is sampled
- **THEN** the outcome is `agrees`, with the number of values, and the record has no level
