## ADDED Requirements

### Requirement: Nested packs
A pack nested in another pack, a built-in pack's package inside another's or a local pack's directory inside another
pack's directory, SHALL build on that pack as if `requires` named it, and selecting it SHALL bring that pack first.

#### Scenario: A local subfield
- **WHEN** a workspace lists `./packs/oncology/radiotherapy`, and `packs/oncology` holds a `pack.yaml`
- **THEN** the packs are `core`, `oncology` and `radiotherapy`, with no `requires` in either

#### Scenario: A built-in subfield
- **WHEN** a workspace lists `particle-physics`, whose package is `veriphy.packs.physics.particle_physics`
- **THEN** `physics` is selected before it
