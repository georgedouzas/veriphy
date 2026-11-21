"""Register the Lean steps, `elaborate` and `level`, and share how a Lean step runs Lean on a generated file."""

from veriphy.packs.lean.steps._lean import (
    ELABORATE,
    LEVEL,
    lean_sources,
    message_line,
    message_text,
    resolve,
    run_lean,
    toolchain,
)
from veriphy.steps import register

register(ELABORATE, LEVEL)

__all__ = [
    'ELABORATE',
    'LEVEL',
    'lean_sources',
    'message_line',
    'message_text',
    'resolve',
    'run_lean',
    'toolchain',
]
