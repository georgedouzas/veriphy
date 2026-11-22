# certificates/meaning-check Specification

## Purpose
Test whether a formal statement says what its informal one meant, which the kernel cannot judge: Sage draws seeded values satisfying the statement's hypotheses and domain conditions and evaluates its conclusion, and the outcome is recorded as evidence that grants no level.

## Requirements

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

### Requirement: Seeded and recorded
The seed, the values, the evaluations and the agent's informal reading when given SHALL be in the record. The same
declaration, seed and reading SHALL give the same outcome.

#### Scenario: Replay
- **WHEN** the step runs twice on the same declaration with the same seed
- **THEN** the second run returns the first record

### Requirement: Undecided is explicit
When fewer than 10 values satisfy the hypotheses after 200 draws, or the statement cannot be evaluated, the outcome
SHALL be `undecided` and SHALL name the reason, such as the hypothesis that rejected most values.

#### Scenario: Narrow hypotheses
- **WHEN** a claim requires `x = π`
- **THEN** the outcome is `undecided` and names that hypothesis

### Requirement: Identities first
When the statement is an equation, the check SHALL try `symbolic_check` under the hypotheses first and record its
answer, falling back to sampling when it is undecided.

#### Scenario: Symbolic agreement
- **WHEN** the claim is `∀ x : ℝ, Real.cos x ^ 2 + Real.sin x ^ 2 = 1`
- **THEN** the record holds `symbolic_check`'s agreement and no sampled values

### Requirement: Playbooks use the check
The `prove` playbook's formalization step and the `research` triage SHALL run the meaning check, and a
`statement-suspect` report SHALL cite the record of the counterexample.

#### Scenario: Suspect statement
- **WHEN** the check finds a counterexample during `prove`
- **THEN** the report is `statement-suspect` and names the record's path
