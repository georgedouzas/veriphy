# Spec Delta

## Purpose

Defines the contract every Sage daemon method follows: how it is registered, how its parameters are parsed, how exact results are encoded and how errors are reported. Also covers the shared exact solvers that certificate methods build on.

## ADDED Requirements

### Requirement: Declarative method registration
Each daemon method SHALL be registered by declaration alongside its implementation, with its name and whether it is advisory. The daemon SHALL dispatch only to registered methods. An unknown method SHALL produce an error response naming the method.

#### Scenario: Unknown method
- **WHEN** a request has `"method": "nosuch"`
- **THEN** the response is `{"id": <id>, "error": "..."}` and the error text contains `nosuch`

### Requirement: Validated polynomial parameters
Variable lists SHALL be non-empty valid identifiers. Polynomial strings SHALL be parsed in `QQ[vars]` before the method body runs. A parameter that fails validation SHALL produce an error response that names the parameter. It SHALL NOT produce a Python traceback.

#### Scenario: Invalid variable name
- **WHEN** a certificate method receives `"vars": ["x0", "1y"]`
- **THEN** the error response names `vars` and the daemon keeps serving the next request

#### Scenario: Polynomial outside the ring
- **WHEN** `"poly"` mentions a variable that is not in `vars`
- **THEN** the error response names `poly`

### Requirement: Exact output encoding
Certificate methods SHALL encode rationals as exact strings (`"n"` or `"n/d"`) and polynomials as term lists (`coeff` plus an exponent vector over `vars`). No floating-point value SHALL appear in a certificate result.

#### Scenario: LP solution with a fractional value
- **WHEN** an exact LP yields the multiplier 1/3
- **THEN** the result encodes it as `"1/3"`

### Requirement: Uniform error reporting
Every failure inside a method SHALL become one error response of the form `<method>: <reason>`, on the same line protocol. The daemon SHALL keep serving after an error.

#### Scenario: Infeasible certificate search
- **WHEN** `farkas` is called on a consistent linear system
- **THEN** the error response starts with `farkas:` and states that no certificate exists

### Requirement: Exact LP helper with empty-problem guards
The shared exact LP helper SHALL solve over the rationals and return either an exact solution or "infeasible". It SHALL NOT raise on an LP with no variables or no constraints: an empty system SHALL be treated as trivially feasible with the empty or zero solution.

#### Scenario: No constraints
- **WHEN** a method builds an LP with zero constraints
- **THEN** the helper returns a feasible solution without invoking the backend in a way that crashes

#### Scenario: Infeasible LP
- **WHEN** the constraints are `t ≤ 0` and `t ≥ 1`
- **THEN** the helper reports infeasible, and the calling method turns that into its own error message

### Requirement: Certify method for agent scripts
The daemon SHALL provide a `certify` method. It takes a serialized problem, a family name and a Sage script. It runs the script in a namespace where the problem is pre-bound, and returns the script's `certificate` value, validated against the family's schema and encoded exactly.

#### Scenario: Script returns a well-formed certificate
- **WHEN** the script assigns `certificate = {"weights": {"h1": 1, "h2": QQ(1)/2}}` for the `inequality` family
- **THEN** the response contains the weights as exact strings, keyed by hypothesis name

#### Scenario: Script forgets to assign a certificate
- **WHEN** the script finishes without defining `certificate`
- **THEN** the error response states that no `certificate` was assigned, and includes the script's captured stdout

#### Scenario: Script references an unknown hypothesis
- **WHEN** the certificate names a hypothesis that is not in the problem
- **THEN** the error response names that hypothesis

### Requirement: Method behavior is preserved
The existing methods (`ping`, `factor`, `sos`, `roots`, `lincomb`, `farkas`, `exists`, `sum`, `symbolic_check`, `matrix_check`, `solve`, `run_script`) SHALL keep their names, parameters and result shapes.

#### Scenario: Ping after the restructure
- **WHEN** a client sends `{"id":1,"method":"ping"}`
- **THEN** the response is `{"id": 1, "result": {"ok": true, "sage": <version>}}`
