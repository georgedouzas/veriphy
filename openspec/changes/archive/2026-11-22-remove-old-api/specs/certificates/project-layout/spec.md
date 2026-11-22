## REMOVED Requirements

### Requirement: Migration from the 0.1.0 layout
**Reason**: The top-level `certificates/` directory of 0.1.0 was kept readable for the releases since; one layout
remains.
**Migration**: `mkdir -p .veriphy && git mv certificates .veriphy/certificates`.
