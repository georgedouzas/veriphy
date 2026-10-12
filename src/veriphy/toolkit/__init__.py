"""Provide the building blocks of Sage scripts that assemble Lean proofs.

A script sees the Lean goal as a `Problem`, finds what the proof needs with the toolkit's search primitives, and
writes the proof with its Lean emitters. Importing this package imports SageMath.
"""

from veriphy.toolkit._problem import Hyp, Problem, create_ring, parse_polynomial, read_problem

__all__ = ['Hyp', 'Problem', 'create_ring', 'parse_polynomial', 'read_problem']
