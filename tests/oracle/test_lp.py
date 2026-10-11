"""Test the exact rational LP helper."""

from sage.all import QQ

from veriphy.oracle import encode, solve_exact_lp


def test_solve_exact_lp_without_variables() -> None:
    """Decide a problem with no variables from its constant rows."""
    assert solve_exact_lp(0) == []
    assert solve_exact_lp(0, les=[([], 1)]) is None


def test_solve_exact_lp_without_constraints() -> None:
    """Return the zero point when nothing constrains it."""
    assert solve_exact_lp(3, nonneg=True) == [0, 0, 0]


def test_solve_exact_lp_constant_rows() -> None:
    """Decide rows with only zero coefficients directly."""
    assert solve_exact_lp(2, eqs=[([0, 0], 0)]) == [0, 0]
    assert solve_exact_lp(2, eqs=[([0, 0], 1)]) is None


def test_solve_exact_lp_infeasible() -> None:
    """Report an infeasible problem as `None`."""
    assert solve_exact_lp(1, les=[([1], 0), ([-1], 1)]) is None


def test_solve_exact_lp_fractional_solution() -> None:
    """Return exact fractional values."""
    sol = solve_exact_lp(1, eqs=[([3], -1)])
    assert sol == [QQ(1) / 3]
    assert encode(sol) == ['1/3']
