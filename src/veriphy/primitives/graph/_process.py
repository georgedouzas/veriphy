"""Run the external programs the research graph needs, git, lake and `oo-horn`, and fetch release assets."""

import urllib.request
from pathlib import Path
from urllib.error import URLError
from urllib.parse import urlparse

from veriphy.core import CheckerError, ToolError
from veriphy.core import _process as core_process

FETCH_SCHEMES = ('https', 'file')
FETCH_TIMEOUT = 300


def find_tool(name: str, purpose: str) -> str:
    """Return the absolute path of a tool on PATH, or raise naming it and what needs it.

    Args:
        name: The tool's name.
        purpose: What needs the tool, for the error message.

    Returns:
        The tool's path.

    Raises:
        CheckerError: When the tool is not on PATH.
    """
    try:
        return core_process.find_tool(name, purpose)
    except ToolError as exc:
        raise CheckerError(str(exc)) from exc


def run_process(command: list[str], cwd: Path | None = None, timeout: float | None = None) -> tuple[int, str, str]:
    """Run a command without a shell and return its exit status, standard output and standard error.

    Args:
        command: The executable's absolute path and its arguments.
        cwd: The working directory.
        timeout: Seconds before the command is stopped, no limit when `None`.

    Returns:
        The exit status, the output and the error output.

    Raises:
        CheckerError: When the command cannot start or does not finish in time.
    """
    try:
        return core_process.run_process(command, cwd, timeout)
    except ToolError as exc:
        raise CheckerError(str(exc)) from exc


def fetch_url(url: str, timeout: float = FETCH_TIMEOUT) -> bytes:
    """Return the bytes an `https` or `file` URL holds.

    Args:
        url: The URL.
        timeout: Seconds before the fetch is stopped.

    Returns:
        The content.

    Raises:
        CheckerError: When the scheme is not `https` or `file`, or the fetch fails.
    """
    if urlparse(url).scheme not in FETCH_SCHEMES:
        message = f'{url}: only https and file URLs are fetched'
        raise CheckerError(message)
    try:
        response = urllib.request.urlopen(url, timeout=timeout)  # noqa: S310  # nosec B310 - scheme checked above
        with response:
            return bytes(response.read())
    except (URLError, OSError) as exc:
        message = f'{url}: {exc}'
        raise CheckerError(message) from exc
