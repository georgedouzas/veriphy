"""Provide the Sage-backed daemon: its protocol entry point and the exact building blocks of its methods.

Importing this package imports SageMath.
"""

from veriphy.oracle._encoding import encode
from veriphy.oracle._lp import solve_exact_lp
from veriphy.oracle._protocol import answer_request

__all__ = ['answer_request', 'encode', 'solve_exact_lp']
