"""Check a formula's dimensions with pint, and a constant's value against CODATA, as SciPy ships it."""

import ast
import math
from collections.abc import Callable

import pint
import scipy
from scipy import constants

UNITS = pint.UnitRegistry()
# functions whose argument must be dimensionless, and what they return
FUNCTIONS: dict[str, Callable[[float], float]] = {
    'exp': math.exp,
    'log': math.log,
    'ln': math.log,
    'sin': math.sin,
    'cos': math.cos,
    'tan': math.tan,
    'sinh': math.sinh,
    'cosh': math.cosh,
    'tanh': math.tanh,
}


class DimensionError(ValueError):
    """Signal a part of a formula whose dimensions don't fit."""


def _evaluate(node: ast.AST, symbols: dict[str, pint.Quantity]) -> pint.Quantity:
    """Return a formula's value with every symbol at 1 of its unit, raising where the dimensions don't fit."""
    if isinstance(node, ast.Constant) and isinstance(node.value, int | float):
        return UNITS.Quantity(float(node.value), 'dimensionless')
    if isinstance(node, ast.Name):
        if node.id not in symbols:
            message = f"the symbol '{node.id}' has no unit: give it one with --unit {node.id}=<unit>"
            raise DimensionError(message)
        return symbols[node.id]
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub | ast.UAdd):
        return _evaluate(node.operand, symbols)
    if isinstance(node, ast.BinOp):
        left, right = _evaluate(node.left, symbols), _evaluate(node.right, symbols)
        try:
            return _combine(node.op, left, right, node)
        except pint.DimensionalityError as exc:
            message = f'{ast.unparse(node)} adds {left.dimensionality} to {right.dimensionality}'
            raise DimensionError(message) from exc
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and len(node.args) == 1:
        return _call(node, node.func.id, _evaluate(node.args[0], symbols))
    message = f'{ast.unparse(node)} is not a formula of numbers, symbols, + - * / **, sqrt and elementary functions'
    raise DimensionError(message)


def _call(node: ast.Call, name: str, argument: pint.Quantity) -> pint.Quantity:
    """Return the value of `sqrt` or an elementary function, whose argument must be dimensionless."""
    if name == 'sqrt':
        return argument**0.5
    if name not in FUNCTIONS:
        message = f'{ast.unparse(node)} is not a formula of numbers, symbols, + - * / **, sqrt and elementary functions'
        raise DimensionError(message)
    if not argument.dimensionless:
        message = f'{ast.unparse(node)} takes {argument.dimensionality}, which is not dimensionless'
        raise DimensionError(message)
    return UNITS.Quantity(1.0, 'dimensionless')


def _combine(op: ast.operator, left: pint.Quantity, right: pint.Quantity, node: ast.BinOp) -> pint.Quantity:
    """Return the result of one arithmetic operation on two quantities."""
    if isinstance(op, ast.Add):
        return left + right
    if isinstance(op, ast.Sub):
        return left - right
    if isinstance(op, ast.Mult):
        return left * right
    if isinstance(op, ast.Div):
        return left / right
    if isinstance(op, ast.Pow) and right.dimensionless:
        return left ** float(right.magnitude)
    message = f'{ast.unparse(node)}: the operator is not supported, or the exponent has dimensions'
    raise DimensionError(message)


def dimensions(inputs: dict[str, object]) -> dict[str, object]:
    """Check that the two sides of a formula have the same dimensions, every symbol at its declared unit.

    Args:
        inputs: `formula`, as `lhs = rhs` in Python syntax, and `units`, each `symbol=unit` in pint's notation.

    Returns:
        `accepted` with the dimensions of the two sides when they agree, `refused` with where they don't otherwise.

    Examples:
        >>> dimensions({'formula': 'E = m * c**2', 'units': ['E=J', 'm=kg', 'c=m/s']})['status']
        'accepted'
        >>> dimensions({'formula': 'E = m * c', 'units': ['E=J', 'm=kg', 'c=m/s']})['status']
        'refused'
    """
    formula = str(inputs['formula'])
    units = inputs.get('units')
    pairs = [str(u).split('=', 1) for u in units] if isinstance(units, list) else []
    # pi is a number, unless the formula gives the symbol a unit of its own
    symbols = {'pi': UNITS.Quantity(1.0, 'dimensionless')}
    symbols |= {name.strip(): UNITS.Quantity(1.0, unit.strip()) for name, unit in pairs}
    if formula.count('=') != 1:
        return {'status': 'failed', 'error': 'write the formula as one equation, lhs = rhs'}
    sides = [ast.parse(side.strip(), mode='eval').body for side in formula.split('=')]
    try:
        left, right = (_evaluate(side, symbols) for side in sides)
    except DimensionError as exc:
        return {'status': 'refused', 'error': str(exc)}
    shown = [str(side.dimensionality) or 'dimensionless' for side in (left, right)]
    if left.dimensionality != right.dimensionality:
        return {
            'status': 'refused',
            'error': f'the left side is {shown[0]} and the right side {shown[1]}',
            'sides': shown,
        }
    return {
        'status': 'accepted',
        'dimensions': shown[0],
        'tools': [{'name': 'pint', 'version': pint.__version__, 'pin': 'version'}],
    }


def constant(inputs: dict[str, object]) -> dict[str, object]:
    """Return the CODATA value of a physical constant, as SciPy ships it, with its unit and uncertainty.

    Args:
        inputs: `name`, the constant's CODATA name, such as `Newtonian constant of gravitation`.

    Returns:
        The value, the unit and the standard uncertainty, or the names that come closest.
    """
    name = str(inputs['name'])
    found = constants.physical_constants.get(name)
    if found is None:
        close = constants.find(name.split(maxsplit=1)[0]) if name.split() else []
        return {'status': 'failed', 'error': f"CODATA has no constant '{name}'; close names: {', '.join(close[:5])}"}
    value, unit, uncertainty = found
    tools = [{'name': 'scipy.constants (CODATA)', 'version': scipy.__version__, 'pin': 'version'}]
    return {'status': 'reported', 'value': value, 'unit': unit, 'uncertainty': uncertainty, 'tools': tools}
