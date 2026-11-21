"""Register the Lean steps, `check` and `level`, and share how a Lean step runs Lean on a generated file."""

from veriphy.packs.lean.steps._lean import (
    CHECK,
    LEVEL,
    lean_sources,
    message_line,
    message_text,
    resolve,
    run_lean,
    toolchain,
)
from veriphy.steps import register

register(CHECK, LEVEL)

__all__ = [
    'CHECK',
    'LEVEL',
    'lean_sources',
    'message_line',
    'message_text',
    'resolve',
    'run_lean',
    'toolchain',
]
