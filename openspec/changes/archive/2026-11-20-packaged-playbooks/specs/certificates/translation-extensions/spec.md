# Spec Delta

## MODIFIED Requirements

### Requirement: Library-specific recipes
Recipes and recipe assets specific to a library SHALL live under `recipes/<library>/` of the packaged playbooks, be indexed in their own section of the recipe index, and be offered only when that library's pack is active.

#### Scenario: Physlib recipe offered
- **WHEN** the `physlib` pack is active and the goal concerns Physlib's `lorentzAlgebra`
- **THEN** the recipe index offers the Physlib Lorentz-algebra recipe alongside the generic `lie_structure`
