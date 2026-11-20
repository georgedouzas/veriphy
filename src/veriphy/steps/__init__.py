"""Run Veriphy's steps: each hashes its inputs, replays a final record of the same inputs, or runs and records.

`python -m veriphy <step>` runs one from the command line. The steps are `elaborate`, `level` and `meaning` (Lean), and
`validate`, `reason` and `report` (the research claim graph).
"""

from veriphy.steps._cli import STEPS, main
from veriphy.steps._graph import REASON, REPORT, VALIDATE
from veriphy.steps._lean import ELABORATE, LEVEL, MEANING, lean_sources
from veriphy.steps._runner import Outcome, Params, Prepared, Result, Step, exit_code, run_step

__all__ = [
    'ELABORATE',
    'LEVEL',
    'MEANING',
    'REASON',
    'REPORT',
    'STEPS',
    'VALIDATE',
    'Outcome',
    'Params',
    'Prepared',
    'Result',
    'Step',
    'exit_code',
    'lean_sources',
    'main',
    'run_step',
]
