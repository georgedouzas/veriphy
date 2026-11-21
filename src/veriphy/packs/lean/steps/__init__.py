"""The `lean` pack's steps, `check` and `level`, are declared in its `pack.yaml`; this package holds their scopes."""

from veriphy.packs.lean.steps._scopes import lean_imports, lean_workspace

__all__ = ['lean_imports', 'lean_workspace']
