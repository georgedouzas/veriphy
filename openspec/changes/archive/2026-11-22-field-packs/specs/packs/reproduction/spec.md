## REMOVED Requirements

### Requirement: Reproduction pack
**Reason**: Replaced by the `social-science` pack, a field rather than a method.
**Migration**: `packs: [social-science]`.

### Requirement: Running an analysis
**Reason**: The analysis runs as a Python script in a fresh process, with no R and no container.
**Migration**: Rewrite the analysis as `run(data, inputs)` in Python, returning `{'estimate': …, 'se': …}`.

### Requirement: Reproduce step
**Reason**: The `social-science` pack's `reproduce` step replaces it.
**Migration**: `veriphy layers step reproduce <script.py> <data> [--sha256 d] [--claimed v]`.

### Requirement: Vary step
**Reason**: Renamed `robustness`, in the `social-science` pack.
**Migration**: `veriphy layers step robustness <script.py> <data> --variation "…"`.

### Requirement: Playbook and skill
**Reason**: The playbook and the `reproduce` skill move to the `social-science` pack.
**Migration**: `veriphy layers agents path --pack social-science`.
