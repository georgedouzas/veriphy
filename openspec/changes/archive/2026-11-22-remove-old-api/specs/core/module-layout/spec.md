## REMOVED Requirements

### Requirement: Deprecated aliases
**Reason**: The module paths before the layered layout were kept for one minor release; the layout is now the only
one.
**Migration**: `veriphy.toolkit` → `veriphy.script`, `veriphy.graph` → `veriphy.claims`, `veriphy.oracle` →
`veriphy.packs.math.primitives.sage.methods`, `veriphy.prompts` → `veriphy.agents`, `veriphy.sage_server` →
`veriphy.packs.math.primitives.sage`, `veriphy.certificates` → `veriphy.packs.math.steps.certificates`,
`veriphy.translations` → `veriphy.packs.math.primitives.translations`; the programs are `veriphy layers <layer>` and `veriphy pack math <program>`.

## ADDED Requirements

### Requirement: No old module paths
The package SHALL contain only the layer modules, the packs and the facades `veriphy`, `veriphy.script` and
`veriphy.__main__`.

#### Scenario: An old import
- **WHEN** a script runs `from veriphy.toolkit import Lean`
- **THEN** it fails with `ModuleNotFoundError`, and `from veriphy.script import Lean` works
