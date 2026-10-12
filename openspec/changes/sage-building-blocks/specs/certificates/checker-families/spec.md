# Spec Delta

## REMOVED Requirements

### Requirement: Fixed family set
**Reason**: Veriphy no longer ships ready-made certificates; agents and users build each certificate with `sage_run`, the toolkit and the procedures.
**Migration**: Proof shapes are built with the toolkit's emitters inside a `sage_run` script; see the procedures.

### Requirement: Identity family
**Reason**: Veriphy no longer ships ready-made certificates; agents and users build each certificate with `sage_run`, the toolkit and the procedures.
**Migration**: Use the ideal-membership and factorization recipes (`linear_combination` and `rw [show … by ring1]` emitters).

### Requirement: Inequality family
**Reason**: Veriphy no longer ships ready-made certificates; agents and users build each certificate with `sage_run`, the toolkit and the procedures.
**Migration**: Use the Farkas, SOS and hint-search recipes (`linear_combination`, `sq_nonneg` and `nlinarith` emitters).

### Requirement: Witness family
**Reason**: Veriphy no longer ships ready-made certificates; agents and users build each certificate with `sage_run`, the toolkit and the procedures.
**Migration**: Use the witness recipe (witness emitter with a `norm_num` side goal).

### Requirement: Sum family
**Reason**: Veriphy no longer ships ready-made certificates; agents and users build each certificate with `sage_run`, the toolkit and the procedures.
**Migration**: Use the sum-by-induction recipe (induction emitter); `#sage_sum` discovery becomes a toolkit primitive.

### Requirement: Cases family
**Reason**: Veriphy no longer ships ready-made certificates; agents and users build each certificate with `sage_run`, the toolkit and the procedures.
**Migration**: Use the case-split recipe, or emit `decide` directly.

### Requirement: Existing tactics preserve their interface
**Reason**: `sage_factor`, `sage_sos`, `sage_lincomb`, `sage_witness`, `sage_sum`, `sage_farkas` and `sage_exists` are removed; their techniques become recipes that create the certificate for each goal.
**Migration**: Committed proofs are unaffected (they contain only emitted replacements). Replace a remaining call with `sage_run` following the matching recipe; the procedures map each removed tactic to its recipe.
