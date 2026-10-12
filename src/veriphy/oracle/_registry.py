"""Register daemon methods and coerce their request parameters."""

from collections.abc import Callable

from veriphy.core import Coercer, JsonObject, JsonValue, Method, MethodError, ParamError, VeriphyError
from veriphy.oracle._encoding import encode

MISSING = object()


def _get_param(pname: str, req: JsonObject, default: object = MISSING) -> object:
    """Return a request parameter, its default, or raise if a required one is missing."""
    if pname in req:
        return req[pname]
    if default is not MISSING:
        return default
    raise ParamError(param=pname, reason='missing')


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
