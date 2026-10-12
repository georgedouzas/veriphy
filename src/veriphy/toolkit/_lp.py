"""Solve exact rational linear programs."""

from collections.abc import Iterable, Sequence

from sage.all import QQ, MixedIntegerLinearProgram
from sage.numerical.mip import MIPSolverException
from sage.rings.rational import Rational

Row = tuple[Sequence[object], object]


def _split_rows(rows: Iterable[Row], *, equality: bool) -> tuple[list[tuple[list[Rational], Rational]], bool]:
    """Return the rows with a nonzero coefficient, and whether every constant row holds."""
    live = []
    for coeffs, const in rows:
        exact = [QQ(c) for c in coeffs]
        constant = QQ(const)
        if any(exact):
            live.append((exact, constant))
        elif (constant != 0) if equality else (constant > 0):
            return live, False
    return live, True


def solve_exact_lp(
    nvars: int,
    eqs: Iterable[Row] = (),
    les: Iterable[Row] = (),
    objective: Sequence[object] | None = None,
    nonneg: bool | Iterable[int] = False,
    *,
    maximize: bool = False,
) -> list[Rational] | None:
    """Solve a linear program exactly over the rationals.

    A row `(coeffs, const)` means `sum(coeffs[j] * t_j) + const`, which is `= 0` in `eqs` and `<= 0` in `les`. A row
    with only zero coefficients is decided directly, and a problem with no variables or no live rows never reaches the
    solver backend.

    Args:
        nvars: The number of variables `t_0 .. t_{nvars-1}`.
        eqs: The equality rows.
        les: The inequality rows.
        objective: The objective coefficients, or `None` for a feasibility problem.
        nonneg: `True` for all variables nonnegative, or the indices of the nonnegative ones.
        maximize: Whether to maximize the objective instead of minimizing it.

    Returns:
        The exact solution, or `None` if the problem is infeasible or unbounded.

    Examples:
        >>> solve_exact_lp(1, eqs=[([3], -1)])
        [1/3]
        >>> solve_exact_lp(1, les=[([1], 0), ([-1], 1)]) is None
        True
    """
    live_eqs, eqs_hold = _split_rows(eqs, equality=True)
    live_les, les_hold = _split_rows(les, equality=False)
    if not (eqs_hold and les_hold):
        return None
    if nvars == 0 or not (live_eqs or live_les):
        return [QQ(0)] * nvars
    lp = MixedIntegerLinearProgram(solver='PPL', maximization=maximize)
    t = lp.new_variable()
    for j in range(nvars) if nonneg is True else (nonneg or ()):
        lp.add_constraint(t[j] >= 0)
    for coeffs, const in live_eqs:
        lp.add_constraint(lp.sum(c * t[j] for j, c in enumerate(coeffs) if c != 0) == -const)
    for coeffs, const in live_les:
        lp.add_constraint(lp.sum(c * t[j] for j, c in enumerate(coeffs) if c != 0) <= -const)
    weights = [QQ(c) for c in objective] if objective is not None else []
    lp.set_objective(lp.sum(c * t[j] for j, c in enumerate(weights) if c != 0) if any(weights) else None)
    try:
        lp.solve()
    except MIPSolverException:
        return None
    return [QQ(lp.get_values(t[j])) for j in range(nvars)]
