"""Define the type vocabulary of the daemon protocol."""

from collections.abc import Callable
from typing import TypeAlias

RELATIONS = ('eq', 'le', 'lt', 'ne')

JsonValue: TypeAlias = bool | int | float | str | list['JsonValue'] | dict[str, 'JsonValue'] | None
JsonObject: TypeAlias = dict[str, JsonValue]
Method: TypeAlias = Callable[[JsonObject], JsonValue]
Coercer: TypeAlias = Callable[[str, JsonObject, dict[str, object]], tuple[str, object]]
