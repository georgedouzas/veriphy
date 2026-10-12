"""Provide the building blocks of Sage scripts that assemble Lean proofs.

A script sees the Lean goal as a `Problem`, finds what the proof needs with the toolkit's search primitives, and
writes the proof with its Lean emitters. Importing this package imports SageMath.
"""

from veriphy.toolkit._lean import Lean, parenthesize, polynomial, rational, tactic, term
from veriphy.toolkit._problem import Hyp, Problem, create_ring, parse_polynomial, read_problem

__all__ = [
    'Hyp',
    'Lean',
    'Problem',
    'create_ring',
    'parenthesize',
    'parse_polynomial',
    'polynomial',
    'rational',
    'read_problem',
    'tactic',
    'term',
]
