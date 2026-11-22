"""Machine-verified physics and math proofs in Lean 4 with SageMath as an untrusted oracle.

The package is built in layers, each importing only the layers below it and `veriphy.core`:

- `veriphy.primitives` (0): deterministic operations on tools, and the claim graph's engines.
- `veriphy.steps` (1): every step hashes its inputs and records its result; `veriphy layers step <step>`.
- `veriphy.claims` (2): the research claim graph, its levels, reasoning and reports.
- `veriphy.workflows` (3): sequences of steps.
- `veriphy.agents` (4): the playbooks agents follow.
- `veriphy.packs`: `core`, `lean` and `math`, each with its `pack.yaml` and the layer subpackages it needs.
- `veriphy.script`: what Sage scripts import.

`veriphy.run(verb, target, **inputs)` runs an operation, the same one `veriphy layers step <verb>` runs in the shell.

Importing `veriphy` itself does not import Sage:

>>> import veriphy
>>> isinstance(veriphy.__version__, str)
True
"""

from veriphy._api import run
from veriphy.core._version import __version__
from veriphy.steps import Result

__all__ = ['Result', '__version__', 'run']
