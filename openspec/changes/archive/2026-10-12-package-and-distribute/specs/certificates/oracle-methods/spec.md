# Spec Delta

## MODIFIED Requirements

### Requirement: Method behavior is preserved
The existing methods (`ping`, `factor`, `sos`, `roots`, `lincomb`, `farkas`, `exists`, `sum`, `symbolic_check`, `matrix_check`, `solve`, `run_script`) SHALL keep their names, parameters and result shapes. Results MAY gain new fields; existing fields SHALL NOT be renamed, removed or change type.

#### Scenario: Ping after the restructure
- **WHEN** a client sends `{"id":1,"method":"ping"}`
- **THEN** the response is `{"id": 1, "result": {"ok": true, "sage": <version>, ...}}`, where `ok` and `sage` keep their meaning and any further fields (such as `veriphy`) are additive
