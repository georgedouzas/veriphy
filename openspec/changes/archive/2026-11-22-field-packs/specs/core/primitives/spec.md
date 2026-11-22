## MODIFIED Requirements

### Requirement: Shipped primitives
Veriphy SHALL ship the framework pack (`horn.check`, `shacl.validate`), the `math` pack (`lean.check`,
`lean.serialize`, `lean.levels`, the `sage` tool, one `sage.*` primitive per Sage method, and the composites `sample`
and `certify`) and the `social-science` pack (the `python` tool, `analysis.exec`, and the composites `analysis.run`
and `analysis.robustness`), each as a `pack.yaml`. The framework pack SHALL NOT need Lean.

#### Scenario: Every Sage method is a primitive
- **WHEN** the Sage session's methods are compared with the `math` pack's primitives
- **THEN** each method has a `sage.*` primitive with an input and an output schema
