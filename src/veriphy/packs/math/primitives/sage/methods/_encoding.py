"""Encode method results as exact JSON."""

from sage.all import QQ, ZZ
from sage.rings.polynomial.multi_polynomial import MPolynomial
from sage.rings.polynomial.polynomial_element import Polynomial
from sage.structure.element import Element

from veriphy.core import EncodingError, JsonValue

MAX_DEPTH = 12


def _encode_polynomial(p: MPolynomial | Polynomial) -> list[JsonValue]:
    """Return a polynomial over QQ as a term list of exact coefficients and exponent vectors."""
    terms: list[JsonValue] = []
    for exps, coeff in sorted(p.dict().items()):
        vector = tuple(exps) if hasattr(exps, '__iter__') else (exps,)
        terms.append({'coeff': str(QQ(coeff)), 'exps': [int(e) for e in vector]})
    return terms


def _encode_container(x: list | tuple | dict, *, advisory: bool, depth: int) -> JsonValue:
    """Return a list, tuple or dict with every element encoded."""
    if isinstance(x, dict):
        return {str(k): encode(v, advisory=advisory, depth=depth + 1) for k, v in x.items()}
    return [encode(v, advisory=advisory, depth=depth + 1) for v in x]


def encode(x: object, *, advisory: bool = False, depth: int = 0) -> JsonValue:
    """Encode a method result exactly as JSON.

    Rationals and integers of Sage become `"n"` or `"n/d"` strings, polynomials become term lists, and containers are
    encoded element by element. Python integers stay integers, since they are structural (exponents, counts).

    Args:
        x: The value to encode.
        advisory: Whether the result is advisory. Advisory results may carry floats and fall back to `str`.
        depth: The current nesting depth.

    Returns:
        The JSON value.

    Raises:
        EncodingError: If a certificate result holds a float, an opaque object, or nests too deeply.

    Examples:
        >>> from sage.all import QQ
        >>> encode({'m': [QQ(-3) / 2, 5]})
        {'m': ['-3/2', 5]}
    """
    if isinstance(x, float) and not advisory:
        message = f'floating-point value {x} in a certificate result'
        raise EncodingError(message)
    if x is None or isinstance(x, bool | str | int | float):
        return x
    if isinstance(x, list | tuple | dict) and depth <= MAX_DEPTH:
        return _encode_container(x, advisory=advisory, depth=depth)
    if isinstance(x, MPolynomial | Polynomial):
        return _encode_polynomial(x)
    if (isinstance(x, Element) and x.parent() in (QQ, ZZ)) or advisory:
        return str(x)
    message = f'cannot encode {type(x).__name__} exactly'
    raise EncodingError(message)
