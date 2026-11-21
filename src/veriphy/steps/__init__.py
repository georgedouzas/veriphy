"""Layer 1, steps: each hashes its inputs, replays a final record of the same inputs, or runs and records.

A step is registered by the layer or pack that defines it, and `veriphy <verb>` runs one. Veriphy's own
packs register `check` and `level` (`lean`), `meaning` (`math`), and `validate`, `reason` and `report` (`core`,
through `veriphy.claims`). This package imports only `veriphy.core` and `veriphy.primitives`.
"""

from veriphy.steps._cli import main
from veriphy.steps._primitives import call_primitive
from veriphy.steps._records import (
    KINDS,
    LEVELLED_KINDS,
    Record,
    RecordStore,
    config_digest,
    input_digest,
    read_record,
)
from veriphy.steps._registry import (
    DEPRECATED_VERBS,
    LAYERS,
    load_steps,
    register,
    registered,
    resolve_verb,
)
from veriphy.steps._runner import Argument, Outcome, Params, Prepared, Result, Step, exit_code, run_step

__all__ = [
    'DEPRECATED_VERBS',
    'KINDS',
    'LAYERS',
    'LEVELLED_KINDS',
    'Argument',
    'Outcome',
    'Params',
    'Prepared',
    'Record',
    'RecordStore',
    'Result',
    'Step',
    'call_primitive',
    'config_digest',
    'exit_code',
    'input_digest',
    'load_steps',
    'main',
    'read_record',
    'register',
    'registered',
    'resolve_verb',
    'run_step',
]
