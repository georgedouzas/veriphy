"""Register the Lean steps, `check` and `level`, and share what a Lean step's digest covers."""

from veriphy.packs.lean.steps._lean import CHECK, LEVEL, lean_sources, resolve
from veriphy.steps import register

register(CHECK, LEVEL, pack='lean')

__all__ = ['CHECK', 'LEVEL', 'lean_sources', 'resolve']
