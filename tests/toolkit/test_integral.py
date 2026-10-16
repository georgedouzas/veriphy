"""Test definite integrals from Sage's antiderivatives."""

import pytest

from veriphy.core import CertificateError
from veriphy.toolkit import Problem, definite_integral_proof, read_problem


def _problem(body: str, lower: str, upper: str, value: str, upper_text: str) -> Problem:
    """Return a problem whose goal is `∫ t in lower..upper, body = value`."""
    integral = f'definite_integral({body}, i0_, {lower}, {upper})'
    return read_problem(
        {
            'vars': [],
            'atoms': [],
            'carrier': 'ℝ',
            'integrals': [
                {
                    'var': 'i0_',
                    'body': body,
                    'lower': lower,
                    'upper': upper,
                    'function': f'fun t => {body}',
                    'lower_text': lower,
                    'upper_text': upper_text,
                },
            ],
            'goal': {'kind': 'rel', 'rel': 'eq', 'expr': f'({integral}) - ({value})', 'text': 'integral'},
        },
    )


def test_cosine_squared_states_the_endpoint_facts() -> None:
    """The antiderivative of cos² needs sin (2 (2π)) = 0, stated with the bound's own text."""
    problem = _problem('cos(i0_)^2', '0', '2*pi', 'pi', '2 * Real.pi')
    proof = str(definite_integral_proof(problem))
    assert 'intervalIntegral.integral_eq_sub_of_hasDerivAt' in proof
    assert 'Real.sin ((2 * (2 * Real.pi) : ℝ)) = 0 := by' in proof


def test_refusals() -> None:
    """A wrong value and a goal without an integral are refused."""
    with pytest.raises(CertificateError, match='the integral is 4/3'):
        definite_integral_proof(_problem('i0_^2 + 2*i0_', '0', '1', '1', '1'))
    with pytest.raises(CertificateError, match='no interval integral'):
        definite_integral_proof(read_problem({'vars': [], 'atoms': [], 'goal': {'kind': 'false'}}))
