# Spec Delta

## REMOVED Requirements

### Requirement: Exact rational literals
**Reason**: Proof text is now built by scripts with the Python emitters, not by Lean-side reconstruction for fixed certificate shapes.
**Migration**: The Python emitters of `certificates/lean-emitters` provide this, with the same guarantees.

### Requirement: Polynomial reconstruction over atoms
**Reason**: As above.
**Migration**: The Python emitters of `certificates/lean-emitters` provide this, with the same guarantees.

### Requirement: Weighted hypothesis sums
**Reason**: As above.
**Migration**: The Python emitters of `certificates/lean-emitters` provide this, with the same guarantees.

### Requirement: Witness tuples
**Reason**: As above.
**Migration**: The Python emitters of `certificates/lean-emitters` provide this, with the same guarantees.

### Requirement: Step sequences
**Reason**: As above.
**Migration**: The Python emitters of `certificates/lean-emitters` provide this, with the same guarantees.

### Requirement: Re-parseable identifiers
**Reason**: As above.
**Migration**: The Python emitters of `certificates/lean-emitters` provide this, with the same guarantees.
