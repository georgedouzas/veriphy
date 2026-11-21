"""Hold the tools and primitives of the installed packs, and call a primitive with its checks around it."""

import atexit
import functools
import importlib
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field, replace
from pathlib import Path

from veriphy.core import PrimitiveError, Resolved, installed, resolve
from veriphy.core._version import __version__
from veriphy.primitives._contracts import (
    Found,
    Session,
    check_pin,
    command_line,
    probe_files,
    run_files,
    start_session,
)
from veriphy.primitives._descriptors import Body, Primitive, Tool, composite_trust, read_primitive, read_tool
from veriphy.primitives._schema import check

# the key under which an output names the tools that produced it
TOOLS_KEY = 'tools'
_COMPOSITES: dict[str, tuple[Primitive, tuple[str, ...], str | None, Body]] = {}


def composite(
    name: str,
    parts: tuple[str, ...],
    *,
    decides: str | None = None,
    input_schema: Mapping[str, object],
    output_schema: Mapping[str, object],
    pack: str,
) -> Callable[[Body], Body]:
    """Return a decorator that registers a function as a composite primitive of the parts it calls.

    The function receives the input and `call(part, input)`, and returns the output. Its trust class is computed
    when a registry loads it: the deciding part's, or the lowest of its parts'.

    Args:
        name: The composite's name.
        parts: The primitives it calls.
        decides: The part whose output decides the result, if any.
        input_schema: Its input's JSON Schema.
        output_schema: Its output's JSON Schema.
        pack: The pack it belongs to.

    Returns:
        The decorator.
    """

    def register(body: Body) -> Body:
        """Register `body`, and return it unchanged."""
        if decides is not None and decides not in parts:
            message = f"composite {name}: the deciding part '{decides}' is not among its parts"
            raise PrimitiveError(message)
        stub = Primitive(name, 'search', input_schema, output_schema, parts=parts, decides=decides, pack=pack)
        _COMPOSITES[name] = (stub, parts, decides, body)
        return body

    return register


@dataclass
class Registry:
    """The tools and primitives Veriphy can run, and the sessions of the JSON-RPC tools it started.

    Args:
        tools: The tools, by name.
        primitives: The primitives, by name.
    """

    tools: dict[str, Tool] = field(default_factory=dict)
    primitives: dict[str, Primitive] = field(default_factory=dict)
    sessions: dict[str, Session] = field(default_factory=dict)

    def get(self, name: str) -> Primitive:
        """Return a primitive by name, or raise naming those there are.

        Args:
            name: The primitive's name.

        Returns:
            The primitive.

        Raises:
            PrimitiveError: If no primitive has the name.
        """
        primitive = self.primitives.get(name)
        if primitive is None:
            message = f"no primitive is named '{name}': the primitives are {', '.join(sorted(self.primitives))}"
            raise PrimitiveError(message)
        return primitive

    def unavailable(self, name: str) -> str | None:
        """Return why a primitive cannot run here (a tool missing), or `None` when it can.

        Args:
            name: The primitive's name.

        Returns:
            The reason, or `None`.
        """
        primitive = self.get(name)
        if primitive.composite:
            reasons = [self.unavailable(part) for part in primitive.parts]
            return next((r for r in reasons if r), None)
        if primitive.function:
            return None
        tool = self.tools.get(primitive.tool)
        if tool is None:
            return f"its tool '{primitive.tool}' is not declared"
        try:
            command_line(tool)
        except PrimitiveError as exc:
            return str(exc)
        return None

    def call(self, name: str, inputs: dict[str, object]) -> dict[str, object]:
        """Call a primitive: check its input, its tool's pin, run it, and check its output.

        Args:
            name: The primitive's name.
            inputs: Its input.

        Returns:
            Its output, with `tools`: the name, version and pin kind of every tool that produced it.
        """
        primitive = self.get(name)
        check(inputs, primitive.input_schema, f'{name} input')
        if primitive.composite:
            output = self._call_composite(primitive, inputs)
        elif primitive.function:
            output = self._call_function(primitive, inputs)
        else:
            found, output = self._call_tool(primitive, inputs)
            output = {**output, TOOLS_KEY: [found.to_json()]}
        check(output, primitive.output_schema, f'{name} output')
        return output

    def _call_function(self, primitive: Primitive, inputs: dict[str, object]) -> dict[str, object]:
        """Call a Python primitive in-process; its tools are Veriphy itself and any it reports under `tools`."""
        module, _, name = primitive.function.partition(':')
        output = dict(getattr(importlib.import_module(module), name)(inputs))
        reported = output.pop(TOOLS_KEY, [])
        own = Found('veriphy', __version__, 'version').to_json()
        return {**output, TOOLS_KEY: [own, *(reported if isinstance(reported, list) else [])]}

    def _call_tool(self, primitive: Primitive, inputs: dict[str, object]) -> tuple[Found, dict[str, object]]:
        """Run a tool primitive by its tool's contract."""
        tool = self.tools.get(primitive.tool)
        if tool is None:
            message = f"primitive {primitive.name}: its tool '{primitive.tool}' is not declared"
            raise PrimitiveError(message)
        if tool.contract == 'files':
            found = check_pin(tool, probe_files(tool))
            seed = inputs.get('seed') if primitive.seed == 'placeholder' else None
            return found, run_files(tool, primitive.command, inputs, seed if isinstance(seed, int) else None)
        session = self.sessions.get(tool.name)
        if session is None:
            session = start_session(tool)
            self.sessions[tool.name] = session
        return session.found, session.request(primitive.method, inputs)

    def _call_composite(self, primitive: Primitive, inputs: dict[str, object]) -> dict[str, object]:
        """Run a composite, calling its parts through the same checks, and gather their tools."""
        _, _, _, body = _COMPOSITES[primitive.name]
        used: list[object] = []

        def call_part(part: str, part_inputs: dict[str, object]) -> dict[str, object]:
            """Call one declared part."""
            if part not in primitive.parts:
                message = f"composite {primitive.name} called '{part}', which is not among its parts"
                raise PrimitiveError(message)
            output = self.call(part, part_inputs)
            tools = output.get(TOOLS_KEY)
            used.extend(tools if isinstance(tools, list) else [])
            return output

        output = body(inputs, call_part)
        unique = [t for i, t in enumerate(used) if t not in used[:i]]
        return {**output, TOOLS_KEY: unique}

    def close(self) -> None:
        """Stop every session this registry started."""
        for session in self.sessions.values():
            session.close()
        self.sessions.clear()


@functools.cache
def default_registry() -> Registry:
    """Return the registry of every installed pack, loaded once per process.

    Returns:
        The registry.
    """
    return load_registry()


def load_registry(packages: Mapping[str, str] | None = None, resolved: Resolved | None = None) -> Registry:
    """Return the registry of a configuration's tools, primitives and composites.

    Args:
        packages: Each pack's name and package, when `resolved` is not given; every installed pack by default.
        resolved: A workspace's resolved configuration, whose packs and sections the registry holds.

    Returns:
        The registry. Its sessions stop when the process exits.

    Raises:
        ModuleNotFoundError: If a pack's `primitives` subpackage imports a module that is not installed.
    """
    config = resolved if resolved is not None else installed(packages)
    registry = Registry()
    for name, spec in config.section('tools').items():
        registry.tools[name] = read_tool(name, _mapping(spec), config.sources.get(f'tools.{name}', ''))
    for name, spec in config.section('primitives').items():
        entry = f'primitives.{name}'
        source = config.sources.get(entry, '')
        registry.primitives[name] = read_primitive(name, _mapping(spec), source, config.directory(entry))
    selected = {pack.name for pack in config.packs}
    for pack in config.packs:
        if pack.package is None:
            continue
        try:
            importlib.import_module(f'{pack.package}.primitives')
        except ModuleNotFoundError as exc:
            if exc.name not in {f'{pack.package}.primitives', pack.package}:
                raise
    for name, (stub, parts, decides, body) in _COMPOSITES.items():
        if stub.pack not in selected or not all(p in registry.primitives for p in parts):
            continue
        trust = composite_trust({p: registry.primitives[p].trust for p in parts}, decides)
        registry.primitives[name] = replace(stub, trust=trust, body=body)
    atexit.register(registry.close)
    return registry


@functools.cache
def workspace_registry(root: Path) -> Registry:
    """Return the registry of a workspace's resolved configuration, loaded once per process.

    Args:
        root: The workspace root.

    Returns:
        The registry.
    """
    return load_registry(resolved=resolve(root))


def _mapping(value: object) -> dict[str, object]:
    """Return a declaration's mapping, empty when absent."""
    return {str(k): v for k, v in value.items()} if isinstance(value, dict) else {}
