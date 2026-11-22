"""The `math` pack's steps are declared in its `pack.yaml`; this package holds their digest scopes and the catalogs."""

from veriphy.packs.math.steps._lean_scopes import lean_imports, lean_workspace

__all__ = ['lean_imports', 'lean_workspace']
