"""Provide the Sage-backed daemon: its protocol entry point and the exact building blocks of its methods.

Importing this package imports SageMath.
"""

from veriphy.packs.math.primitives.sage.methods._encoding import encode
from veriphy.packs.math.primitives.sage.methods._protocol import answer_request
from veriphy.packs.math.primitives.sage.methods._scripts import run_test_script

__all__ = ['answer_request', 'encode', 'run_test_script']
