"""Check a claimed property of a metric with EinsteinPy: that it solves the vacuum equations, is flat, or has a scalar.

The metric is a SymPy matrix over the given coordinates, `diag(...)` or `[[...], ...]`, and every other name in it is a
constant. EinsteinPy computes its curvature, and SymPy simplifies what must vanish. When SymPy cannot reduce an
expression to zero, the check evaluates it at random points: a value away from zero refuses the claim, and values that
all vanish leave it `undecided`, since a numerical zero is not a proof.
"""

import random

import sympy as sp

# where an expression SymPy cannot simplify is evaluated, and how small a value counts as zero there
POINTS, ZERO = 5, 1e-9
PROPERTIES = 'vacuum (the Ricci tensor vanishes), flat (the Riemann tensor vanishes), or R = <expression>'


def _metric(inputs: dict[str, object]) -> tuple[sp.Matrix, list[sp.Symbol]]:
    """Return the metric and its coordinates, read with SymPy."""
    coordinates = list(sp.symbols(str(inputs['coordinates'])))
    names = {str(c): c for c in coordinates}
    metric = sp.Matrix(sp.sympify(str(inputs['metric']), locals=names | {'diag': sp.diag}))
    return metric, coordinates


def _residuals(inputs: dict[str, object], metric: sp.Matrix, coordinates: list[sp.Symbol]) -> list[sp.Expr]:
    """Return the expressions the claimed property says vanish."""
    from einsteinpy.symbolic import (  # noqa: PLC0415 - the pack's optional library, imported when the check runs
        MetricTensor,
        RicciScalar,
        RicciTensor,
        RiemannCurvatureTensor,
    )

    tensor = MetricTensor(metric.tolist(), coordinates)
    claimed = str(inputs['property']).strip()
    if claimed == 'vacuum':
        return list(sp.Array(RicciTensor.from_metric(tensor).tensor()).reshape(len(coordinates) ** 2))
    if claimed == 'flat':
        return list(sp.Array(RiemannCurvatureTensor.from_metric(tensor).tensor()).reshape(len(coordinates) ** 4))
    if claimed.startswith('R') and '=' in claimed:
        names = {str(c): c for c in coordinates} | {str(s): s for s in metric.free_symbols}
        scalar = sp.sympify(claimed.split('=', 1)[1], locals=names)
        return [RicciScalar.from_metric(tensor).expr - scalar]
    message = f"the property '{claimed}' is not one of {PROPERTIES}"
    raise ValueError(message)


def _nonzero(expression: sp.Expr) -> dict[str, float] | None:
    """Return a point where an expression is away from zero, or None when it vanishes at every point tried."""
    symbols = sorted(expression.free_symbols, key=str)
    draw = random.Random(0)  # noqa: S311  # nosec B311 - repeatable points to evaluate at, not a secret
    for _ in range(POINTS):
        point = {s: sp.Rational(draw.randint(11, 97), draw.randint(3, 9)) for s in symbols}
        value = complex(sp.N(expression.subs(point)))
        if abs(value) > ZERO:
            return {str(s): float(v) for s, v in point.items()}
    return None


def curvature(inputs: dict[str, object]) -> dict[str, object]:
    """Check a claimed property of a metric: vacuum, flat, or a Ricci scalar.

    Args:
        inputs: `coordinates`, as `t r theta phi`, `metric`, as `diag(...)` or a nested list over them, and
            `property`: `vacuum`, `flat`, or `R = <expression>`.

    Returns:
        `accepted` when SymPy reduces every residual to zero, `refused` with a point where one is not zero, and
        `undecided` when one doesn't simplify but vanishes at every point tried.

    Examples:
        >>> curvature({'coordinates': 't x', 'metric': 'diag(-1, 1)', 'property': 'flat'})['status']
        'accepted'
        >>> curvature({'coordinates': 't r', 'metric': 'diag(-r, 1)', 'property': 'R = 0'})['status']
        'refused'
    """
    import einsteinpy  # noqa: PLC0415 - the pack's optional library, imported only when the check runs

    try:
        metric, coordinates = _metric(inputs)
        residuals = _residuals(inputs, metric, coordinates)
    except (sp.SympifyError, ValueError, TypeError) as exc:
        return {'status': 'failed', 'error': str(exc)}
    if metric.shape != (len(coordinates), len(coordinates)):
        return {'status': 'failed', 'error': f'the metric is {metric.shape}, for {len(coordinates)} coordinates'}
    tools = [
        {'name': 'einsteinpy', 'version': einsteinpy.__version__, 'pin': 'version'},
        {'name': 'sympy', 'version': sp.__version__, 'pin': 'version'},
    ]
    unsimplified = [r for r in (sp.simplify(r) for r in residuals) if r != 0]
    for residual in unsimplified:
        point = _nonzero(residual)
        if point is not None:
            error = f'{sp.sstr(residual)} is not zero: at {point}'
            return {'status': 'refused', 'error': error, 'residual': sp.sstr(residual), 'tools': tools}
    if unsimplified:
        shown = sp.sstr(unsimplified[0])
        return {'status': 'undecided', 'error': f'{shown} vanishes at {POINTS} points, but SymPy does not simplify it'}
    return {'status': 'accepted', 'tools': tools}
