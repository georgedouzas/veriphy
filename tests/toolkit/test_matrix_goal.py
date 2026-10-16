"""Test matrix goals read from the goal, with and without side relations."""

import pytest

from veriphy.core import CertificateError
from veriphy.toolkit import Problem, matrix_from_goal_proof, read_problem

BOOST = (
    '((matrix(SR, [[cosh(x0), sinh(x0)], [sinh(x0), cosh(x0)]])).transpose().__mul__(matrix(SR, [[1, 0], [0, -1]]))'
    '.__mul__(matrix(SR, [[cosh(x0), sinh(x0)], [sinh(x0), cosh(x0)]]))) - (matrix(SR, [[1, 0], [0, -1]]))'
)
SQUARE = (
    '((matrix(SR, [[cosh(x0), sinh(x0)], [sinh(x0), cosh(x0)]])).transpose()'
    '.__mul__(matrix(SR, [[cosh(x0), sinh(x0)], [sinh(x0), cosh(x0)]]))) - (1)'
)
EIGEN = (
    '(matrix(SR, [[2, 1, 0], [1, 2, 1], [0, 1, 2]]).__mul__(matrix(SR, [[1], [sqrt(2)], [1]])))'
    ' - ((2 + sqrt(2)) * matrix(SR, [[1], [sqrt(2)], [1]]))'
)


def _problem(expr: str) -> Problem:
    """Return a problem over a real atom `u` whose goal's symbolic form is `expr`."""
    return read_problem(
        {
            'vars': ['x0'],
            'atoms': ['u'],
            'atom_types': ['ℝ'],
            'carrier': 'ℝ',
            'goal': {'kind': 'rel', 'rel': 'eq', 'expr': expr, 'text': 'lhs = rhs'},
        },
    )


def test_boost_closes_by_the_hyperbolic_identity() -> None:
    """Each entry of Λᵀ η Λ - η closes by a multiple of `Real.cosh_sq_sub_sinh_sq u`."""
    problem = _problem(BOOST)
    proof = str(matrix_from_goal_proof(problem.goal, problem, relations=['Real.cosh_sq_sub_sinh_sq']))
    assert 'linear_combination ((1 : ℝ)) * (Real.cosh_sq_sub_sinh_sq (u : ℝ))' in proof
    assert proof.startswith('first\n| ext i j')


def test_square_roots_are_kept_opaque() -> None:
    """Sage simplifies (√2)² itself, but Lean does not: the relation is still applied, with its condition."""
    problem = _problem(EIGEN)
    proof = str(matrix_from_goal_proof(problem.goal, problem, relations=['Real.sq_sqrt']))
    assert 'Real.sq_sqrt (show (0 : ℝ) ≤ (2 : ℝ) by positivity)' in proof


def test_refusals() -> None:
    """A false identity, an identity that needs relations, and an unknown relation are refused."""
    problem = _problem(SQUARE)
    with pytest.raises(CertificateError, match='the identity is false'):
        matrix_from_goal_proof(problem.goal, problem, relations=['Real.cosh_sq_sub_sinh_sq'])
    problem = _problem(BOOST)
    with pytest.raises(CertificateError, match='only by identities of their functions'):
        matrix_from_goal_proof(problem.goal, problem)
    with pytest.raises(CertificateError, match='unknown side relation'):
        matrix_from_goal_proof(problem.goal, problem, relations=['Real.tan_eq_sin_div_cos'])
