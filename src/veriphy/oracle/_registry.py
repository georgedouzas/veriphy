"""Register daemon methods and coerce their request parameters."""

from collections.abc import Callable

from sage.all import QQ, PolynomialRing
from sage.rings.polynomial.multi_polynomial import MPolynomial
from sage.rings.polynomial.polynomial_element import Polynomial
from sage.structure.parent import Parent

from veriphy.core import RELATIONS, Coercer, JsonObject, JsonValue, Method, MethodError, ParamError, VeriphyError
from veriphy.oracle._encoding import encode
from veriphy.toolkit import create_ring, parse_polynomial

MISSING = object()


def _get_param(pname: str, req: JsonObject, default: object = MISSING) -> object:
    """Return a request parameter, its default, or raise if a required one is missing."""
    if pname in req:
        return req[pname]
    if default is not MISSING:
        return default
    raise ParamError(param=pname, reason='missing')


def _coerce_ring(pname: str, req: JsonObject, ctx: dict[str, object]) -> tuple[str, object]:
    """Return the multivariate ring QQ[vars] for a non-empty list of identifiers, passed as `R`."""
    names = _get_param(pname, req)
    if not isinstance(names, list) or not names:
        raise ParamError(param=pname, reason='must be a non-empty list of identifiers')
    bad = [n for n in names if not isinstance(n, str) or not n.isidentifier()]
    if bad:
        raise ParamError(param=pname, reason=f'not valid identifiers: {bad}')
    ring = create_ring(names)
    ctx['R'] = ring
    return 'R', ring


def _coerce_univariate_ring(pname: str, req: JsonObject, ctx: dict[str, object]) -> tuple[str, object]:
    """Return the univariate ring QQ[var] for one identifier, passed as `R`."""
    name = _get_param(pname, req)
    if not isinstance(name, str) or not name.isidentifier():
        raise ParamError(param=pname, reason='must be an identifier')
    ctx['R'] = PolynomialRing(QQ, name)
    return 'R', ctx['R']


def _parse_poly(pname: str, s: object, ctx: dict[str, object]) -> MPolynomial | Polynomial:
    """Return a polynomial string parsed in the ring a previous coercer built."""
    ring = ctx.get('R')
    if not isinstance(ring, Parent):
        raise ParamError(param=pname, reason='declared before the variables')
    return parse_polynomial(ring, s, param=pname)


def _coerce_poly(pname: str, req: JsonObject, ctx: dict[str, object]) -> tuple[str, object]:
    """Return one polynomial parameter parsed in the current ring."""
    return pname, _parse_poly(pname, _get_param(pname, req), ctx)


def _coerce_poly_list(pname: str, req: JsonObject, ctx: dict[str, object]) -> tuple[str, object]:
    """Return a list of polynomial parameters parsed in the current ring, empty when absent."""
    items = _get_param(pname, req, [])
    if not isinstance(items, list):
        raise ParamError(param=pname, reason='must be a list of polynomial strings')
    return pname, [_parse_poly(pname, s, ctx) for s in items]


def _coerce_relations(*allowed: str) -> Coercer:
    """Return a coercer for a list of relation tags drawn from `allowed` (all relations when empty)."""
    tags = allowed or RELATIONS

    def coerce(pname: str, req: JsonObject, _ctx: dict[str, object]) -> tuple[str, object]:
        """Return the relation tags, rejecting any outside the allowed set."""
        items = _get_param(pname, req)
        if not isinstance(items, list) or any(r not in tags for r in items):
            raise ParamError(param=pname, reason=f'must be a list of relations in {list(tags)}')
        return pname, items

    return coerce


def _coerce_str(pname: str, req: JsonObject, _ctx: dict[str, object]) -> tuple[str, object]:
    """Return a string parameter."""
    value = _get_param(pname, req)
    if not isinstance(value, str):
        raise ParamError(param=pname, reason='must be a string')
    return pname, value


def _coerce_int(default: int) -> Coercer:
    """Return a coercer for an integer parameter with a default."""

    def coerce(pname: str, req: JsonObject, _ctx: dict[str, object]) -> tuple[str, object]:
        """Return the integer parameter or its default."""
        value = _get_param(pname, req, default)
        if isinstance(value, bool) or not isinstance(value, int | str):
            raise ParamError(param=pname, reason='must be an integer')
        try:
            return pname, int(value)
        except ValueError as exc:
            raise ParamError(param=pname, reason='must be an integer') from exc

    return coerce


def _coerce_json(pname: str, req: JsonObject, _ctx: dict[str, object]) -> tuple[str, object]:
    """Return a parameter unchanged."""
    return pname, _get_param(pname, req)


def _coerce_all(params: dict[str, Coercer], req: JsonObject) -> dict[str, object]:
    """Return the keyword arguments for a method body, coerced in declaration order."""
    ctx: dict[str, object] = {}
    kwargs = {}
    for pname, coerce in params.items():
        key, value = coerce(pname, req, ctx)
        kwargs[key] = value
    return kwargs


def _register_method(
    table: dict[str, Method],
    name: str,
    *,
    advisory: bool = False,
    raw: bool = False,
    **params: Coercer,
) -> Callable[[Callable[..., object]], Method]:
    """Return a decorator that registers a method body under `name` in the module's method `table`."""

    def register(body: Callable[..., object]) -> Method:
        """Register `body`, wrapped with parameter coercion, exact encoding and `<method>: <reason>` errors."""

        def run(req: JsonObject) -> JsonValue:
            """Run the method on one request's parameters."""
            try:
                out = body(req) if raw else body(**_coerce_all(params, req))
                return encode(out, advisory=advisory)
            except VeriphyError as exc:
                message = f'{name}: {exc}'
                raise MethodError(message) from exc
            except Exception as exc:
                message = f'{name}: {type(exc).__name__}: {exc}'
                raise MethodError(message) from exc

        run.__doc__ = body.__doc__
        table[name] = run
        return run

    return register
