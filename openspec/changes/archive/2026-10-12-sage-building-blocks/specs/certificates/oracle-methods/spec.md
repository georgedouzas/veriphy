# Spec Delta

## REMOVED Requirements

### Requirement: Certify method for agent scripts
**Reason**: `sage_certify` is removed; the `run` method executes certificate scripts and returns Lean text.
**Migration**: Call `run` with the script; validation of the result is Lean's check of the emitted proof.

## MODIFIED Requirements

### Requirement: Method behavior is preserved
The daemon methods SHALL be `ping`, `run`, `run_script`, `symbolic_check`, `matrix_check` and `solve`. The certificate-search methods of the removed tactics (`factor`, `sos`, `roots`, `lincomb`, `farkas`, `exists`, `sum`) SHALL be removed, their algorithms living on as toolkit primitives. Remaining methods keep their parameters and result shapes; results MAY gain fields, and existing fields SHALL NOT be renamed, removed or change type.

#### Scenario: Ping after the restructure
- **WHEN** a client sends `{"id":1,"method":"ping"}`
- **THEN** the response is `{"id": 1, "result": {"ok": true, "sage": <version>, ...}}`, where `ok` and `sage` keep their meaning and any further fields (such as `veriphy`) are additive

#### Scenario: Removed method
- **WHEN** a client sends `{"id":2,"method":"farkas","params":{}}`
- **THEN** the response is an unknown-method error naming `farkas`
