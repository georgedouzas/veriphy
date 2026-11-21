"""Layer 3, workflows: sequences of steps, written as data, whose next step follows from the target's records.

`veriphy next <workflow> <target>` names the next step, and `veriphy run` runs the steps that are not an agent's until
an agent step or the end. This package imports only the layers below it and `veriphy.core`.
"""

from veriphy.workflows._engine import Next, next_step, run_workflow

__all__ = ['Next', 'next_step', 'run_workflow']
