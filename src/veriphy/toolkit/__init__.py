"""Provide the building blocks of Sage scripts that assemble Lean proofs.

A script sees the Lean goal as a `Problem`, finds what the proof needs with the toolkit's search primitives, and
writes the proof with its Lean emitters. Importing this package imports SageMath.
"""

from veriphy.toolkit._emit import (
    by_cases,
    calc_chain,
    combination,
    decide,
    field_simp,
    fresh_name,
    hyp,
    linear_combination,
    mul_nonneg,
    mul_pos,
    negate_goal,
    nlinarith,
    norm_num,
    positivity,
    rcases,
    refute,
    rewrite_by,
    sq_nonneg,
    steps,
    sum_by_induction,
    witness,
)
from veriphy.toolkit._lean import Lean, parenthesize, polynomial, rational, tactic, term
from veriphy.toolkit._lp import solve_exact_lp
from veriphy.toolkit._problem import Hyp, Problem, Side, create_ring, parse_polynomial, read_problem
from veriphy.toolkit._sos import sos_decomposition

__all__ = [
    'Hyp',
    'Lean',
    'Problem',
    'Side',
    'by_cases',
    'calc_chain',
    'combination',
    'create_ring',
    'decide',
    'field_simp',
    'fresh_name',
    'hyp',
    'linear_combination',
    'mul_nonneg',
    'mul_pos',
    'negate_goal',
    'nlinarith',
    'norm_num',
    'parenthesize',
    'parse_polynomial',
    'polynomial',
    'positivity',
    'rational',
    'rcases',
    'read_problem',
    'refute',
    'rewrite_by',
    'solve_exact_lp',
    'sos_decomposition',
    'sq_nonneg',
    'steps',
    'sum_by_induction',
    'tactic',
    'term',
    'witness',
]
