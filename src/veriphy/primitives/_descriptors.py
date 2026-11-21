"""Describe tools and primitives as a pack's `pack.yaml` declares them, with their pins, schemas and trust classes."""

import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from pathlib import Path

from veriphy.core import TRUST_CLASSES, PrimitiveError

CONTRACTS = ('files',)
PIN_KINDS = ('image', 'commit', 'version')
# a composite's code: it receives the input and a function calling a part by name
Body = Callable[[dict[str, object], Callable[[str, dict[str, object]], dict[str, object]]], dict[str, object]]
SEED_KINDS = ('param', 'placeholder')


@dataclass(frozen=True)
class Pin:
    """What a tool must be before it runs.

    Args:
        kind: `image` (a container digest), `commit` (a fetched release, with its SHA-256) or `version`.
        value: The image with its digest, the commit, or the exact version.
        sha256: The release's digest, for a `commit` pin.
    """

    kind: str
    value: str
    sha256: str = ''


@dataclass(frozen=True)
class VersionProbe:
    """How a tool reports its version.

    Args:
        command: The arguments that print it, after the tool's command.
        pattern: A regular expression whose first group is the version, in what the tool printed.
    """

    command: tuple[str, ...] = ()
    pattern: str = r'(\d+(?:\.\d+)+)'


@dataclass(frozen=True)
class Tool:
    """A program Veriphy starts.

    Args:
        name: The tool's name.
        contract: `files`: a command, run once per call, writing one JSON result.
        run: The command, as an argument list; placeholders such as `{out}` are paths Veriphy writes.
        pin: What the tool must be, or `None` for a tool its pack does not pin yet.
        version: How the tool reports its version.
        timeout: Seconds before a call is stopped.
        pack: The pack that declares the tool.
    """

    name: str
    contract: str
    run: tuple[str, ...]
    pin: Pin | None = None
    version: VersionProbe = field(default_factory=VersionProbe)
    timeout: float = 600.0
    pack: str = ''


@dataclass(frozen=True)
class Primitive:
    """One typed operation on a tool, or a composite of other primitives.

    Args:
        name: The primitive's name, as `sage.sample`.
        trust: Its trust class; a composite's is computed from its parts.
        input_schema: The JSON Schema its input must satisfy.
        output_schema: The JSON Schema its output must satisfy.
        tool: The tool it runs on, empty for a composite.
        function: A Python `module:function`, called in-process, instead of a tool.
        command: The arguments after the tool's command, for a files tool.
        seed: How a random primitive takes its seed: `param` (the input's `seed`) or `placeholder` (`{seed}`).
        parts: A composite's parts, by name.
        decides: The part whose output decides a composite's result, if any.
        body: A composite's code: it receives the input and a function calling a part by name.
        pack: The pack that declares the primitive.
    """

    name: str
    trust: str
    input_schema: Mapping[str, object]
    output_schema: Mapping[str, object]
    tool: str = ''
    function: str = ''
    command: tuple[str, ...] = ()
    seed: str | None = None
    parts: tuple[str, ...] = ()
    decides: str | None = None
    body: (
        Callable[[dict[str, object], Callable[[str, dict[str, object]], dict[str, object]]], dict[str, object]] | None
    ) = None
    pack: str = ''

    @property
    def composite(self) -> bool:
        """Whether the primitive is a composition of other primitives."""
        return self.body is not None


def composite_trust(parts: Mapping[str, str], decides: str | None) -> str:
    """Return a composite's trust class: its deciding part's, or the lowest of its parts' without one.

    Args:
        parts: Each part's trust class, by name.
        decides: The deciding part, if any.

    Returns:
        The class.

    Examples:
        >>> composite_trust({'sage.search': 'search', 'lean.check': 'kernel'}, 'lean.check')
        'kernel'
        >>> composite_trust({'lean.serialize': 'kernel', 'sage.sample': 'oracle'}, None)
        'oracle'
    """
    if decides is not None:
        return parts[decides]
    return min(parts.values(), key=TRUST_CLASSES.index)


def _choice(value: object, allowed: tuple[str, ...], what: str, where: str) -> str:
    """Return a declared value when it is one of the allowed ones, or raise naming them."""
    if value not in allowed:
        message = f"{where}: {what} '{value}' is not one of {', '.join(allowed)}"
        raise PrimitiveError(message)
    return str(value)


def _strings(value: object, what: str, where: str) -> tuple[str, ...]:
    """Return a declared list of strings, or raise naming the declaration."""
    if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
        message = f'{where}: {what} must be a list of strings, as [sage, -python, -m, …]'
        raise PrimitiveError(message)
    return tuple(value)


def _pin(spec: object, where: str) -> Pin | None:
    """Return a declared pin: `{version: …}`, `{commit: …, sha256: …}` or `{image: …}`."""
    if spec is None:
        return None
    if not isinstance(spec, dict) or len(set(spec) & set(PIN_KINDS)) != 1:
        message = f'{where}: pin must name one of {", ".join(PIN_KINDS)}, as {{version: "10.9"}}'
        raise PrimitiveError(message)
    kind = next(k for k in PIN_KINDS if k in spec)
    if kind == 'commit' and not spec.get('sha256'):
        message = f'{where}: a commit pin needs the release sha256'
        raise PrimitiveError(message)
    return Pin(kind, str(spec[kind]), str(spec.get('sha256', '')))


def read_tool(name: str, spec: Mapping[str, object], pack: str) -> Tool:
    """Return a tool from its `pack.yaml` declaration.

    Args:
        name: The tool's name.
        spec: Its declaration.
        pack: The declaring pack.

    Returns:
        The tool.
    """
    where = f'tool {name} ({pack})'
    raw = spec.get('version')
    version = raw if isinstance(raw, dict) else {}
    probe = VersionProbe(
        command=_strings(version.get('command', []), 'version.command', where),
        pattern=str(version.get('pattern', VersionProbe.pattern)),
    )
    timeout = spec.get('timeout', 600)
    return Tool(
        name=name,
        contract=_choice(spec.get('contract'), CONTRACTS, 'contract', where),
        run=_strings(spec.get('run'), 'run', where),
        pin=_pin(spec.get('pin'), where),
        version=probe,
        timeout=float(timeout) if isinstance(timeout, int | float) else 600.0,
        pack=pack,
    )


def read_schema(base: Path, spec: object, where: str) -> Mapping[str, object]:
    """Return a schema declared inline or as a path relative to the pack's directory.

    Args:
        base: The pack's directory.
        spec: The declaration: a mapping, or a path to a JSON file.
        where: The declaration's place, for errors.

    Returns:
        The schema.

    Raises:
        PrimitiveError: If the schema is missing or does not read.
    """
    if isinstance(spec, dict):
        return spec
    if not isinstance(spec, str):
        message = f'{where}: give the schema inline, or as a path relative to the pack'
        raise PrimitiveError(message)
    path = base / spec
    try:
        value = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        message = f'{where}: the schema {path} does not read: {exc}'
        raise PrimitiveError(message) from exc
    if not isinstance(value, dict):
        message = f'{where}: the schema {path} must be a JSON object'
        raise PrimitiveError(message)
    return value


def read_primitive(name: str, spec: Mapping[str, object], pack: str, base: Path) -> Primitive:
    """Return a tool primitive from its `pack.yaml` declaration; composites are registered from code.

    Args:
        name: The primitive's name.
        spec: Its declaration.
        pack: The declaring pack.
        base: The pack's directory, against which schema paths resolve.

    Returns:
        The primitive.
    """
    where = f'primitive {name} ({pack})'
    seed = spec.get('seed')
    return Primitive(
        name=name,
        trust=_choice(spec.get('trust'), TRUST_CLASSES, 'trust class', where),
        input_schema=read_schema(base, spec.get('input'), where + ' input'),
        output_schema=read_schema(base, spec.get('output'), where + ' output'),
        tool=str(spec.get('tool', '')),
        function=str(spec.get('function', '')),
        command=_strings(spec.get('command', []), 'command', where),
        seed=None if seed is None else _choice(seed, SEED_KINDS, 'seed', where),
        pack=pack,
    )
