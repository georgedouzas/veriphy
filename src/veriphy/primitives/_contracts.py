"""Run tools by the `files` contract, one process per call writing one JSON result, checking their pins; no shell."""

import functools
import json
import os
import re
import shlex
import shutil
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

from veriphy.core import PinError, PrimitiveError, ToolError, run_process
from veriphy.primitives._descriptors import Pin, Tool

CONTAINER_RUNTIMES = ('podman', 'docker')
ENV_TOKEN = re.compile(r'\{env:([A-Z_][A-Z0-9_]*)\|(.*)\}')
PLACEHOLDER = re.compile(r'\{(input|out|seed|file:[A-Za-z_][A-Za-z0-9_]*)\}')


@dataclass(frozen=True)
class Found:
    """What a tool reported about itself before it ran.

    Args:
        tool: The tool's name.
        version: The version it reported, or the pinned commit or image.
        pin: The pin kind that was checked, `none` when the tool is not pinned.
    """

    tool: str
    version: str
    pin: str

    def to_json(self) -> dict[str, str]:
        """Return the fields every output carries."""
        return {'name': self.tool, 'version': self.version, 'pin': self.pin}


def command_line(tool: Tool) -> list[str]:
    """Return a tool's command with its tokens resolved.

    `{python}` is this interpreter, and `{env:NAME|default}` the variable `NAME` when set, else `default`, each split
    into arguments.

    Args:
        tool: The tool.

    Returns:
        The command, its program first as an absolute path.

    Raises:
        PrimitiveError: If the program is not installed.

    Examples:
        >>> import os
        >>> os.environ.pop('VERIPHY_EXAMPLE', None) and None
        >>> command_line(Tool('t', 'files', ('{python}', '{env:VERIPHY_EXAMPLE|-c pass}')))[1:]
        ['-c', 'pass']
    """
    resolved: list[str] = []
    for part in tool.run:
        match = ENV_TOKEN.fullmatch(part)
        if part == '{python}':
            resolved.append(sys.executable)
        elif match is not None:
            resolved.extend(shlex.split(os.environ.get(match.group(1)) or match.group(2)))
        else:
            resolved.append(part)
    found = shutil.which(resolved[0])
    if found is None:
        message = f"tool '{tool.name}' is not installed: '{resolved[0]}' is not on the path"
        raise PrimitiveError(message)
    return [found, *resolved[1:]]


def executable(tool: Tool) -> str:
    """Return the path of a tool's program, or raise naming the tool.

    Args:
        tool: The tool.

    Returns:
        The program's absolute path.
    """
    return command_line(tool)[0]


def _match_version(tool: Tool, text: str) -> str:
    """Return the version a tool printed, by its probe's pattern."""
    match = re.search(tool.version.pattern, text)
    if match is None:
        message = f"tool '{tool.name}' did not report a version matching {tool.version.pattern!r}: {text[:200]}"
        raise PrimitiveError(message)
    return match.group(1)


def check_pin(tool: Tool, reported: str | None) -> Found:
    """Check a tool against its pin, and return what was found.

    A `version` pin compares the reported version; `commit` and `image` pins are checked where the tool is fetched or
    started, so here they only name themselves.

    Args:
        tool: The tool.
        reported: The version the tool reported, when it was probed.

    Returns:
        What was found.

    Raises:
        PinError: If the reported version differs from the pinned one.

    Examples:
        >>> sage = Tool('sage', 'files', ('sage',), Pin('version', '10.9'))
        >>> check_pin(sage, '10.9').pin
        'version'
        >>> check_pin(sage, '10.8')  # doctest: +ELLIPSIS
        Traceback (most recent call last):
        ...
        veriphy.core._errors.PinError: tool 'sage' is pinned at version 10.9, and 10.8 was found: ...
    """
    pin: Pin | None = tool.pin
    if pin is None:
        return Found(tool.name, reported or 'unknown', 'none')
    if pin.kind == 'version' and reported != pin.value:
        message = (
            f"tool '{tool.name}' is pinned at version {pin.value}, and {reported} was found: "
            f'install {pin.value}, or change the pin'
        )
        raise PinError(message)
    return Found(tool.name, reported if pin.kind == 'version' and reported else pin.value, pin.kind)


def _arguments(template: tuple[str, ...], paths: dict[str, str], inputs: dict[str, object]) -> list[str]:
    """Return a command with its placeholders replaced by paths Veriphy wrote or files the input names."""

    def replace(match: re.Match[str]) -> str:
        """Return what one placeholder stands for."""
        key = match.group(1)
        if key.startswith('file:'):
            name = key.removeprefix('file:')
            value = inputs.get(name)
            if not isinstance(value, str) or not Path(value).is_file():
                message = f"the input '{name}' must name an existing file, got {value!r}"
                raise PrimitiveError(message)
            return str(Path(value).resolve())
        return paths[key]

    return [PLACEHOLDER.sub(replace, part) for part in template]


def container_runtime() -> str | None:
    """Return the container runtime on the path, `podman` or `docker`, or `None` when there is neither."""
    return next((found for name in CONTAINER_RUNTIMES if (found := shutil.which(name))), None)


def _argv(
    tool: Tool,
    command: tuple[str, ...],
    paths: dict[str, str],
    inputs: dict[str, object],
    directory: Path,
) -> list[str]:
    """Return a files tool's argument list: run directly, or in its pinned image with its files mounted."""
    if tool.pin is None or tool.pin.kind != 'image':
        base = command_line(tool)
        return [base[0], *_arguments(tuple(base[1:]) + command, paths, inputs)]
    runtime = container_runtime()
    if runtime is None:
        message = f"tool '{tool.name}' is pinned to the image {tool.pin.value}, which needs podman or docker"
        raise PinError(message)
    arguments = _arguments(tool.run + command, paths, inputs)
    mounts = {str(directory)} | {str(Path(a).parent) for a in arguments if Path(a).is_absolute() and Path(a).is_file()}
    volumes = [part for mount in sorted(mounts) for part in ('-v', f'{mount}:{mount}')]
    return [runtime, 'run', '--rm', '--network', 'none', *volumes, '-w', str(directory), tool.pin.value, *arguments]


def run_files(tool: Tool, command: tuple[str, ...], inputs: dict[str, object], seed: int | None) -> dict[str, object]:
    """Run a files tool: its input as `{input}`, files the input names as `{file:<name>}`, its result in `{out}`.

    Args:
        tool: The tool.
        command: The primitive's arguments after the tool's command.
        inputs: The primitive's input.
        seed: The seed, for `{seed}`.

    Returns:
        The JSON object the tool wrote to `{out}`.

    Raises:
        PrimitiveError: If the tool fails, writes no result, or writes one that is not a JSON object.
    """
    with tempfile.TemporaryDirectory(prefix='veriphy-') as tmp:
        directory = Path(tmp)
        (directory / 'input.json').write_text(json.dumps(inputs, sort_keys=True))
        paths = {'input': str(directory / 'input.json'), 'out': str(directory / 'out.json'), 'seed': str(seed or 0)}
        argv = _argv(tool, command, paths, inputs, directory)
        try:
            code, out, err = run_process(argv, directory, tool.timeout)
        except ToolError as exc:
            raise PrimitiveError(str(exc)) from exc
        result = directory / 'out.json'
        if code != 0 or not result.is_file():
            detail = (err or out).strip()[-4000:]
            message = (
                f"tool '{tool.name}' exited with status {code} and {'a' if result.is_file() else 'no'} result: {detail}"
            )
            raise PrimitiveError(message)
        try:
            value = json.loads(result.read_text())
        except json.JSONDecodeError as exc:
            message = f"tool '{tool.name}' wrote a result that is not JSON: {exc}"
            raise PrimitiveError(message) from exc
    if not isinstance(value, dict):
        message = f"tool '{tool.name}' must write a JSON object to {{out}}"
        raise PrimitiveError(message)
    return value


@functools.cache
def probe_files(tool: Tool) -> str | None:
    """Return the version a files tool's probe reports, once per process; `None` without a probe or in an image."""
    if not tool.version.command or (tool.pin is not None and tool.pin.kind == 'image'):
        return None
    try:
        _, out, err = run_process([*command_line(tool), *tool.version.command], None, 60)
    except ToolError as exc:
        raise PrimitiveError(str(exc)) from exc
    return _match_version(tool, out + err)
