# core/trust Specification

## Purpose
Give every primitive one of six fixed trust classes and every level the class that grants it, contributed by the packs in one order from `none`, so that a step grants only a level its primitive's class can grant and every report names the class beside the level.

## Requirements

### Requirement: Trust classes
The trust classes SHALL be `kernel`, `checker`, `reproduction`, `oracle`, `measurement` and `search`, fixed by the
schema. `measurement` and `search` SHALL grant no level. A config that names another class SHALL be refused.

#### Scenario: An invented class
- **WHEN** a pack declares a primitive with `trust: certified`
- **THEN** `config check` fails, naming the primitive and the six classes

### Requirement: Levels from packs
Each level SHALL be declared by a pack or the workspace file with its trust class and the level directly below it,
and the levels of a workspace SHALL form one chain from `none`. When two levels name the same level below them,
`config check` SHALL fail naming both, unless the workspace file orders them.

#### Scenario: Default levels
- **WHEN** a workspace has no `veriphy.yaml`
- **THEN** `config show` lists `none`, `oracle-test`, `kernel-test`, `lean-proof` and `certificate` in that order, each
  with its class and pack

#### Scenario: Two fields
- **WHEN** a workspace selects `math` and `reproduction`, which both place a level directly above `none`
- **THEN** `config check` names `oracle-test` and `reproduced`, and passes once `veriphy.yaml` sets
  `levels: {reproduced: {above: oracle-test}, kernel-test: {above: robust}}`

### Requirement: Grant rule
A step SHALL grant only levels of its primitive's trust class. `config check` SHALL refuse a step whose `grants`
breaks the rule, and the step runner SHALL refuse to write such a record.

#### Scenario: Wrong class
- **WHEN** a step over `r.run` (class `reproduction`) declares `grants: [lean-proof]`
- **THEN** `config check` fails, naming the step, the level and both classes

#### Scenario: Evidence grants nothing
- **WHEN** the `meaning` step's record is written
- **THEN** it carries no level, whatever its outcome

### Requirement: Classes in reports
Every report that shows a level SHALL show its trust class beside it.

#### Scenario: A reproduced claim
- **WHEN** the level report lists a claim at `reproduced`
- **THEN** it reads `reproduced (reproduction)`

### Requirement: Claims without Lean
The claim graph, reasoning and reports SHALL work in a workspace without the `lean` pack, with the levels its packs
declare.

#### Scenario: Core alone
- **WHEN** a workspace lists `packs: [core]` and runs `reason` and `report` on a graph
- **THEN** both succeed, and every claim's level is `none`
