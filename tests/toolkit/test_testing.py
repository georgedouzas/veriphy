"""Test the instances of `sage_test`: kernel and oracle instances, the sampler and the default cases."""

import pytest
from sage.all import AA, QQ, RDF, I, QQbar, RealIntervalField, pi

from veriphy.core import CertificateError
from veriphy.toolkit import Sampler, check_instances, default_cases, kernel_instance, oracle_instance


def test_oracle_instances_compare_exactly_or_by_intervals() -> None:
    """Exact values compare exactly; intervals decide inequalities for every point and equality by overlap."""
    assert oracle_instance('2', lhs=QQ(4), rhs=QQ(2) ** 2).verdict
    assert not oracle_instance('2', lhs=QQ(4), rhs=QQ(5), relation='>').verdict
    r = RealIntervalField(64)
    instance = oracle_instance('1', lhs=1 + r(1), rhs=r(1).exp(), relation='<=')
    assert instance.verdict
    assert 'at 64 bits' in instance.evaluation


def test_oracle_refusals() -> None:
    """Floating-point values, low precision and unknown relations are refused."""
    with pytest.raises(CertificateError, match='floating-point'):
        oracle_instance('1', lhs=RDF(1), rhs=RDF(1))
    with pytest.raises(CertificateError, match='at least 53 bits'):
        oracle_instance('1', lhs=RealIntervalField(20)(1), rhs=RealIntervalField(20)(1))
    with pytest.raises(CertificateError, match='unknown relation'):
        oracle_instance('1', lhs=QQ(1), rhs=QQ(1), relation='≈')


def test_oracle_instance_accepts_exact_algebraic_reals() -> None:
    """Exact algebraic numbers (AA, QQbar) compare exactly; they are not floating-point."""
    assert oracle_instance('3', lhs=abs(QQbar(3 + 4 * I)), rhs=AA(5)).verdict
    assert oracle_instance('2', lhs=AA(2).sqrt() ** 2, rhs=QQ(2)).verdict


def test_instance_edge_flag_is_a_bool() -> None:
    """A symbolic truth value passed as `edge` is stored as a Python bool, so the instance encodes."""
    assert kernel_instance('0', proof='norm_num', edge=(pi / 4 == 0)).edge is False
    assert oracle_instance('0', lhs=QQ(0), rhs=QQ(0), edge=(pi / 2 == pi - pi / 2)).edge is True


def test_sampler_is_seeded() -> None:
    """The same seed gives the same values."""
    assert Sampler(3).matrix(2) == Sampler(3).matrix(2)


def test_default_cases_start_with_an_edge_case() -> None:
    """Scalars and dependent matrices get an edge case first; other binder types are refused."""
    cases = default_cases([('n', 'ℕ'), ('A', 'Matrix (Fin n) (Fin n) ℚ')], Sampler(0))
    assert cases[0] == (['0', '(0 : Matrix (Fin 0) (Fin 0) ℚ)'], True)
    assert default_cases([('x', 'ℚ')], Sampler(0))[0] == (['0'], True)
    with pytest.raises(CertificateError, match='no default instances'):
        default_cases([('f', 'ℝ → ℝ')], Sampler(0))


def test_instances_need_a_value_per_binder() -> None:
    """An instance with the wrong number of values, or not built by the helpers, is refused."""
    good = kernel_instance('0', proof='norm_num', edge=True)
    assert check_instances([good], 1) == [good]
    with pytest.raises(CertificateError, match='gives 1 values for 2 binders'):
        check_instances([good], 2)
    with pytest.raises(CertificateError, match='not built with kernel_instance'):
        check_instances(['0'], 1)
