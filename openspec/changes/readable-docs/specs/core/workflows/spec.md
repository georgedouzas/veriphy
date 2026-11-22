## ADDED Requirements

### Requirement: A workflow's target names every step's record

`workflow run` SHALL refuse to continue when a step it ran wrote a record whose inputs don't name the target. It SHALL
say that the target must be each step's first input, and name that input.

#### Scenario: The target is not the script

- **WHEN** `workflow run reproduce-analysis claims.ttl --script analysis.py --data survey.csv` runs `reproduce`
- **THEN** it stops with exit status 1, saying that the target must be each step's first input, here its `script`
