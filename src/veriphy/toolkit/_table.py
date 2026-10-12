"""Read translation tables: the core (`mathlib`), library packs and a project's `.veriphy/translations/`.

The schema is the one `Veriphy.Kit.Table` declares in Lean. The core table ships as `core_table.json`, and a Lean
test keeps it equal to the Lean copy.
"""

import json
from dataclasses import dataclass
from functools import cache
from importlib.resources import files

from veriphy.core import TableError

CORE_TABLE_FILE = 'core_table.json'
PACKS_DIR = 'packs'
ROLES = ('derivative', 'partial')
CONDITION_KINDS = ('ne', 'nonneg', 'pos', 'le')


@dataclass(frozen=True)
class CondSpec:
    """Hold a domain condition an entry imposes.

    Args:
        kind: `ne`, `nonneg` or `pos` on the argument `arg`, or `le` between `lhs` and `rhs`.
        arg: The argument index for a single-term condition.
        lhs: The left side of an `le` condition: an argument (`#i`) or a numeral.
        rhs: The right side of an `le` condition.
    """

    kind: str
    arg: int | None = None
    lhs: str | None = None
    rhs: str | None = None


@dataclass(frozen=True)
class FunctionEntry:
    """Hold a function entry: a Lean constant applied to its last `arity` arguments, `sage(…)` in Sage.

    Args:
        lean: The Lean constant.
        sage: The Sage function name.
        arity: The number of explicit arguments.
        types: The argument types it applies to, any when empty.
        result: The result type.
        conditions: The domain conditions on its arguments.
        example: A Lean term over variables, for the round-trip check.
        role: `None` for a function, `derivative` for `(f, point)`, `partial` for `(coordinate, f, point)`.
    """

    lean: str
    sage: str
    arity: int
    types: tuple[str, ...] = ()
    result: str = ''
    conditions: tuple[CondSpec, ...] = ()
    example: str = ''
    role: str | None = None


@dataclass(frozen=True)
class ConstantEntry:
    """Hold a constant entry such as `Real.pi`.

    Args:
        lean: The Lean constant.
        sage: The Sage name.
        type: Its type.
    """

    lean: str
    sage: str
    type: str


@dataclass(frozen=True)
class RewriteEntry:
    """Hold a rewrite entry: a named lemma, the functions it applies to, its direction and side conditions.

    Args:
        lemma: The lemma name.
        functions: The Sage function names it applies to.
        reverse: Rewrite right to left.
        side: Its side conditions, as Lean text the script fills in.
        example: A worked example goal.
    """

    lemma: str
    functions: tuple[str, ...]
    reverse: bool = False
    side: tuple[str, ...] = ()
    example: str = ''


@dataclass(frozen=True)
class Table:
    """Hold one namespace's entries.

    Args:
        namespace: `mathlib`, a library pack's name, or `project`.
        functions: The function entries.
        constants: The constant entries.
        coercions: The coercions translated as their argument.
        rewrites: The rewrite entries.
        conventions: The conventions the namespace fixes, as `(key, value)` pairs.
    """

    namespace: str
    functions: tuple[FunctionEntry, ...] = ()
    constants: tuple[ConstantEntry, ...] = ()
    coercions: tuple[str, ...] = ()
    rewrites: tuple[RewriteEntry, ...] = ()
    conventions: tuple[tuple[str, str], ...] = ()


def _missing(obj: dict[str, object], key: str, source: str) -> None:
    """Raise when a required field is absent."""
    if obj.get(key) is None:
        raise TableError(source, key, 'missing field')


def _text(obj: dict[str, object], key: str, source: str, default: str | None = None) -> str:
    """Return a string field, required unless a default is given."""
    if default is not None and obj.get(key) is None:
        return default
    _missing(obj, key, source)
    value = obj[key]
    if not isinstance(value, str):
        raise TableError(source, key, 'must be a string')
    return value


def _maybe_text(obj: dict[str, object], key: str, source: str) -> str | None:
    """Return an optional string field."""
    return None if obj.get(key) is None else _text(obj, key, source)


def _count(obj: dict[str, object], key: str, source: str, *, required: bool) -> int | None:
    """Return a natural-number field."""
    if not required and obj.get(key) is None:
        return None
    _missing(obj, key, source)
    value = obj[key]
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise TableError(source, key, 'must be a natural number')
    return value


def _flag(obj: dict[str, object], key: str, source: str) -> bool:
    """Return an optional boolean field, false when absent."""
    value = obj.get(key, False)
    if not isinstance(value, bool):
        raise TableError(source, key, 'must be true or false')
    return value


def _list(obj: dict[str, object], key: str, source: str) -> list[object]:
    """Return an optional list field, empty when absent."""
    value = obj.get(key)
    if value is None:
        return []
    if not isinstance(value, list):
        raise TableError(source, key, 'must be a list')
    return value


def _strings(obj: dict[str, object], key: str, source: str) -> tuple[str, ...]:
    """Return an optional list of strings."""
    items = _list(obj, key, source)
    strings = tuple(i for i in items if isinstance(i, str))
    if len(strings) != len(items):
        raise TableError(source, key, 'must be a list of strings')
    return strings


def _objects(obj: dict[str, object], key: str, source: str) -> list[dict[str, object]]:
    """Return an optional list of JSON objects."""
    items = _list(obj, key, source)
    objects = [i for i in items if isinstance(i, dict)]
    if len(objects) != len(items):
        raise TableError(source, key, 'must be a list of objects')
    return objects


def _condition(obj: dict[str, object], source: str) -> CondSpec:
    """Parse one condition."""
    kind = _text(obj, 'kind', source)
    if kind not in CONDITION_KINDS:
        raise TableError(source, 'kind', f'must be one of {list(CONDITION_KINDS)}, got {kind!r}')
    return CondSpec(
        kind,
        _count(obj, 'arg', source, required=False),
        _maybe_text(obj, 'lhs', source),
        _maybe_text(obj, 'rhs', source),
    )


def _function(obj: dict[str, object], source: str) -> FunctionEntry:
    """Parse one function entry."""
    arity = _count(obj, 'arity', source, required=True)
    return FunctionEntry(
        lean=_text(obj, 'lean', source),
        sage=_text(obj, 'sage', source),
        arity=arity or 0,
        types=_strings(obj, 'types', source),
        result=_text(obj, 'result', source, ''),
        conditions=tuple(_condition(c, source) for c in _objects(obj, 'conditions', source)),
        example=_text(obj, 'example', source, ''),
        role=_role(obj, source),
    )


def _role(obj: dict[str, object], source: str) -> str | None:
    """Return a function entry's role, `None` for an ordinary function."""
    role = _maybe_text(obj, 'role', source)
    if role is not None and role not in ROLES:
        raise TableError(source, 'role', f'must be one of {list(ROLES)}, got {role!r}')
    return role


def _convention(obj: dict[str, object], source: str) -> tuple[str, str]:
    """Parse one convention."""
    return _text(obj, 'key', source), _text(obj, 'value', source)


def _constant(obj: dict[str, object], source: str) -> ConstantEntry:
    """Parse one constant entry."""
    return ConstantEntry(_text(obj, 'lean', source), _text(obj, 'sage', source), _text(obj, 'type', source))


def _rewrite(obj: dict[str, object], source: str) -> RewriteEntry:
    """Parse one rewrite entry."""
    _missing(obj, 'functions', source)
    return RewriteEntry(
        lemma=_text(obj, 'lemma', source),
        functions=_strings(obj, 'functions', source),
        reverse=_flag(obj, 'reverse', source),
        side=_strings(obj, 'side', source),
        example=_text(obj, 'example', source, ''),
    )


def parse_table(data: object, source: str) -> Table:
    """Validate a table read from JSON against the schema and return it.

    Args:
        data: The parsed JSON.
        source: Where it came from (a file name), named in errors.

    Returns:
        The table.

    Raises:
        TableError: If a field is missing or of the wrong kind, naming the source and the field.

    Examples:
        >>> parse_table({'namespace': 'project', 'functions': [{'lean': 'Real.cosh', 'arity': 1}]}, 'cosh.json')
        Traceback (most recent call last):
        ...
        veriphy.core._errors.TableError: cosh.json: missing field 'sage'
        >>> table = parse_table({'namespace': 'project',
        ...     'functions': [{'lean': 'Real.cosh', 'sage': 'cosh', 'arity': 1, 'types': ['ℝ']}]}, 'cosh.json')
        >>> table.functions[0].sage, table.functions[0].types
        ('cosh', ('ℝ',))
    """
    if not isinstance(data, dict):
        raise TableError(source, '<root>', 'must be a JSON object')
    return Table(
        namespace=_text(data, 'namespace', source),
        functions=tuple(_function(f, source) for f in _objects(data, 'functions', source)),
        constants=tuple(_constant(c, source) for c in _objects(data, 'constants', source)),
        coercions=_strings(data, 'coercions', source),
        rewrites=tuple(_rewrite(r, source) for r in _objects(data, 'rewrites', source)),
        conventions=tuple(_convention(c, source) for c in _objects(data, 'conventions', source)),
    )


@cache
def load_core_table() -> Table:
    """Return the core (`mathlib`) table shipped with the toolkit.

    Returns:
        The core table.

    Examples:
        >>> core = load_core_table()
        >>> core.namespace, [f.lean for f in core.functions if f.sage == 'exp']
        ('mathlib', ['Real.exp', 'Complex.exp'])
    """
    text = files('veriphy.toolkit').joinpath(CORE_TABLE_FILE).read_text(encoding='utf-8')
    return parse_table(json.loads(text), CORE_TABLE_FILE)


@cache
def load_pack(name: str) -> Table:
    """Return a library pack shipped with the toolkit, by its namespace.

    Args:
        name: The pack's namespace, such as `physlib`.

    Returns:
        The pack's table.

    Raises:
        TableError: If no pack has that name.

    Examples:
        >>> physlib = load_pack('physlib')
        >>> [f.lean for f in physlib.functions], dict(physlib.conventions)['metric_signature']
        (['Time.deriv', 'Space.deriv'], '+---')
    """
    source = f'{PACKS_DIR}/{name}.json'
    resource = files('veriphy.toolkit').joinpath(PACKS_DIR, f'{name}.json')
    if not resource.is_file():
        raise TableError(source, 'namespace', 'no such pack')
    return parse_table(json.loads(resource.read_text(encoding='utf-8')), source)
