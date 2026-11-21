"""Check a primitive's input and output against their JSON Schemas, naming the field that does not fit."""

from collections.abc import Mapping

from jsonschema import Draft202012Validator

from veriphy.core import PrimitiveError


def check(value: object, schema: Mapping[str, object], what: str) -> None:
    """Raise unless `value` satisfies `schema`, naming the first field that does not and what it must be.

    Args:
        value: The input or output.
        schema: Its JSON Schema (draft 2020-12).
        what: What the value is, as `sage.sample input`, for the message.

    Raises:
        PrimitiveError: If the value does not satisfy the schema.

    Examples:
        >>> check({'values': 10}, {'properties': {'values': {'type': 'integer'}}}, 'x input')
        >>> check({'values': 'ten'}, {'properties': {'values': {'type': 'integer'}}}, 'x input')
        Traceback (most recent call last):
        ...
        veriphy.core._errors.PrimitiveError: x input: `values`: 'ten' is not of type 'integer'
    """
    errors = sorted(Draft202012Validator(schema).iter_errors(value), key=lambda e: list(e.path))
    if not errors:
        return
    error = errors[0]
    place = '.'.join(str(part) for part in error.path) or '(the whole value)'
    message = f'{what}: `{place}`: {error.message}'
    raise PrimitiveError(message)
