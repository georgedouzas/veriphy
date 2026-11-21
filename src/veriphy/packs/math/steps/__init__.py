"""Register the `math` pack's step, `meaning`, and catalog a project's saved certificate scripts."""

from veriphy.packs.math.steps._meaning import MEANING
from veriphy.steps import register

register(MEANING)

__all__ = ['MEANING']
