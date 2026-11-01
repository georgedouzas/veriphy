"""Run the external programs the research graph needs: git, lake, the installer and `oo-horn`."""

import shutil
import subprocess  # nosec B404 - every command is a list of fixed arguments, never a shell
from pathlib import Path

from veriphy.core import CheckerError


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
    path = shutil.which(name)
    if path is None:
        message = f'`{name}` is not on PATH: {purpose}'
        raise CheckerError(message)
    return path


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
        result = subprocess.run(  # noqa: S603  # nosec B603 - fixed argument lists, never a shell
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        message = f'{" ".join(command)}: {exc}'
        raise CheckerError(message) from exc
    return result.returncode, result.stdout, result.stderr
