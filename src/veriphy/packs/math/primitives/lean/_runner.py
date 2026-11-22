"""Run Lean on a source of a workspace: one `lake env lean --json` process per run, with no process kept."""

import json
from dataclasses import dataclass
from pathlib import Path

from veriphy.core import content_digest, find_tool, project_dir, run_process

TIMEOUT_S = 1800


@dataclass(frozen=True)
class Message:
    """One message Lean gave, at its line in the source it was given.

    Args:
        severity: `error`, `warning` or `information`.
        line: The line, from 1.
        text: The message.
    """

    severity: str
    line: int
    text: str


def lake() -> str:
    """Return the path of `lake`, or fail naming what is missing."""
    return find_tool('lake', 'install Lean with elan (https://leanprover-community.github.io/get_started.html)')


def toolchain(root: Path) -> str:
    """Return the workspace's Lean toolchain, as `lean-toolchain` names it."""
    path = root / 'lean-toolchain'
    return path.read_text().strip() if path.is_file() else 'unknown'


def _lean_messages(stdout: str) -> list[Message]:
    """Return the messages `lean --json` printed, one JSON object per line."""
    found = []
    for line in stdout.splitlines():
        if not line.startswith('{'):
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            pos = value.get('pos')
            row = pos.get('line', 0) if isinstance(pos, dict) else 0
            found.append(Message(str(value.get('severity', '')), int(row), str(value.get('data', ''))))
    return found


def run_lean(root: Path, source: str) -> tuple[int, str, list[Message]]:
    """Run `lake env lean --json` on a source written under `.veriphy/runs/tmp/`, and delete it after.

    Args:
        root: The workspace root.
        source: The Lean source.

    Returns:
        The exit status, the error output, and the messages.
    """
    directory = project_dir(root) / 'runs' / 'tmp'
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f'lean-{content_digest(source)[:12]}.lean'
    path.write_text(source)
    try:
        code, stdout, stderr = run_process([lake(), 'env', 'lean', '--json', str(path)], root, TIMEOUT_S)
    finally:
        path.unlink(missing_ok=True)
    return code, stderr or stdout, _lean_messages(stdout)
