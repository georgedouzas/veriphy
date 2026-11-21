"""Run Sage's methods: one call per process for the primitives, or the session Lean keeps while compiling a file."""

from veriphy.packs.math.primitives.sage._session import main

__all__ = ['main']
