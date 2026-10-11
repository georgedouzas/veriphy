"""Machine-verified physics and math proofs in Lean 4 with SageMath as an untrusted oracle.

The Python package is the Sage side of Veriphy. It is a daemon that speaks one JSON request per line on stdin and one
JSON response per line on stdout. The Lean bridge starts it as `sage -python -m veriphy.sage_server`. Every answer is
a certificate that a Lean checker re-verifies, so nothing here is trusted.

- `veriphy.oracle` holds the daemon methods and their building blocks. It requires SageMath.
- `veriphy.sage_server` is the runner that serves the protocol.
- `veriphy.core` holds the named exceptions.

Importing `veriphy` itself does not import Sage:

>>> import veriphy
>>> isinstance(veriphy.__version__, str)
True
"""

from veriphy.core._version import __version__

__all__ = ['__version__']
