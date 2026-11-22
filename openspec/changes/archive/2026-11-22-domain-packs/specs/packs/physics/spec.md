## ADDED Requirements

### Requirement: Physics pack
Veriphy SHALL ship a `physics` pack whose step `check-units` evaluates both sides of a formula with pint, from each
symbol's unit, granting `dimensionally-consistent` (checker) when their dimensions agree and refusing with both sides'
dimensions otherwise, and whose step `check-constant` compares a value with SciPy's CODATA constant, recording SciPy's
version, as evidence. Its conventions SHALL be `metric-signature`, `unit-system` and `fourier-sign`.

#### Scenario: A formula with the wrong dimensions
- **WHEN** `check-units "E = m * c"` runs with `E=J`, `m=kg`, `c=m/s`
- **THEN** it is refused, naming the dimensions of both sides
