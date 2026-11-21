"""Run Lean on a source of a workspace: in a kept REPL environment per import header, or one `lake env lean` per run.

The REPL is `leanprover-community/repl`, pinned by commit and built against the workspace's toolchain on first use,
in the cache. `VERIPHY_LEAN_REPL` names a REPL binary instead, or `off` to run `lake env lean` every time, and
`VERIPHY_LEAN_REPL_SETUP=off` stops the first-use setup. Both ways give the same messages for the same source.
"""

import json
import os
import re
import subprocess  # nosec B404 - a long-lived process started from fixed arguments, never a shell
from dataclasses import dataclass, field
from pathlib import Path

from veriphy.core import ToolError, content_digest, find_tool, project_dir, run_process

TIMEOUT_S = 1800
REPL_REPOSITORY = 'https://github.com/leanprover-community/repl'
# the release tag `v4.34.0`; it builds against the 4.34 toolchains
REPL_COMMIT = '193cf4bb9a22bb3fc6d25774f0fe6a70db1fd6ee'
REPL_VARIABLE = 'VERIPHY_LEAN_REPL'
SETUP_VARIABLE = 'VERIPHY_LEAN_REPL_SETUP'
OFF = frozenset({'0', 'off', 'false', 'no'})
HEADER = re.compile(r'\A(?:\s|--[^\n]*\n|/-(?:.|\n)*?-/)*(?:import [^\n]+\n?(?:\s|--[^\n]*\n)*)*')


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


def split_header(source: str) -> tuple[str, str]:
    r"""Return a source's header (its leading comments and imports) and its body.

    Args:
        source: The Lean source.

    Returns:
        The header and the body; together they are the source.

    Examples:
        >>> split_header('import Lean\nimport Mathlib\n\ndef x := 1\n')
        ('import Lean\nimport Mathlib\n\n', 'def x := 1\n')
    """
    match = HEADER.match(source)
    end = match.end() if match else 0
    return source[:end], source[end:]


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


def run_file(root: Path, source: str) -> tuple[int, str, list[Message]]:
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


def _cache() -> Path:
    """Return Veriphy's cache directory."""
    base = os.environ.get('XDG_CACHE_HOME') or str(Path.home() / '.cache')
    return Path(base) / 'veriphy' / 'lean-repl'


def repl_binary(root: Path) -> Path | None:
    """Return the REPL to use for the workspace's toolchain, setting it up on first use; `None` to run files instead.

    Args:
        root: The workspace root.

    Returns:
        The REPL binary, or `None` when it is off, or cannot be set up.
    """
    named = os.environ.get(REPL_VARIABLE, '')
    if named.lower() in OFF:
        return None
    if named:
        return Path(named)
    chain = toolchain(root)
    directory = _cache() / f'{REPL_COMMIT[:12]}-{re.sub(r"[^A-Za-z0-9.]+", "-", chain)}'
    binary = directory / '.lake' / 'build' / 'bin' / 'repl'
    if binary.is_file():
        return binary
    if os.environ.get(SETUP_VARIABLE, '').lower() in OFF or chain == 'unknown':
        return None
    return _build_repl(directory, chain, binary)


def _build_repl(directory: Path, chain: str, binary: Path) -> Path | None:
    """Fetch the pinned REPL commit and build it against `chain`, returning the binary or `None` if that fails."""
    git = find_tool('git', 'install git to set up the Lean REPL')
    directory.mkdir(parents=True, exist_ok=True)
    steps = [
        [git, 'init', '-q'],
        [git, 'fetch', '-q', '--depth', '1', REPL_REPOSITORY, REPL_COMMIT],
        [git, 'checkout', '-q', 'FETCH_HEAD'],
    ]
    try:
        for step in steps:
            if run_process(step, directory, 600)[0] != 0:
                return None
        (directory / 'lean-toolchain').write_text(chain + '\n')
        if run_process([lake(), 'build'], directory, TIMEOUT_S)[0] != 0:
            return None
    except ToolError:
        return None
    return binary if binary.is_file() else None


@dataclass
class Repl:
    """One REPL process for a workspace, keeping one environment per import header.

    Args:
        root: The workspace root.
        process: The REPL, run under `lake env` in the workspace.
    """

    root: Path
    process: subprocess.Popen[str]
    environments: dict[str, int] = field(default_factory=dict)

    def _send(self, command: dict[str, object]) -> dict[str, object]:
        """Send one command and return the REPL's answer, which ends at a blank line."""
        stdin, stdout = self.process.stdin, self.process.stdout
        if stdin is None or stdout is None or self.process.poll() is not None:
            message = 'the Lean REPL is not running'
            raise ToolError(message)
        stdin.write(json.dumps(command) + '\n\n')
        stdin.flush()
        lines = []
        while (line := stdout.readline()) not in {'\n', ''}:
            lines.append(line)
        if not lines:
            message = 'the Lean REPL exited without answering'
            raise ToolError(message)
        answer = json.loads(''.join(lines))
        if not isinstance(answer, dict):
            message = 'the Lean REPL answered with something other than an object'
            raise ToolError(message)
        return answer

    def run(self, source: str) -> list[Message]:
        """Run a source: its header in a kept environment, its body in that environment.

        Args:
            source: The Lean source.

        Returns:
            The messages, at their lines in the source.

        Raises:
            ToolError: If the REPL fails.
        """
        header, body = split_header(source)
        environment = self.environments.get(header)
        if environment is None:
            answer = self._send({'cmd': header})
            if 'env' not in answer:
                message = f"the Lean REPL could not load the imports: {answer.get('message', answer)}"
                raise ToolError(message)
            environment = int(str(answer['env']))
            self.environments[header] = environment
        answer = self._send({'cmd': body, 'env': environment})
        if 'message' in answer and 'env' not in answer:
            return [Message('error', 1 + header.count('\n'), str(answer['message']))]
        shift = header.count('\n')
        found = []
        listed = answer.get('messages')
        for message in listed if isinstance(listed, list) else []:
            pos = message.get('pos', {}) if isinstance(message, dict) else {}
            severity = str(message.get('severity', '')) if isinstance(message, dict) else ''
            found.append(
                Message(
                    'information' if severity == 'info' else severity,
                    int(pos.get('line', 0)) + shift,
                    str(message.get('data', '')) if isinstance(message, dict) else '',
                ),
            )
        return found

    def close(self) -> None:
        """Stop the REPL."""
        if self.process.stdin is not None:
            self.process.stdin.close()
        try:
            self.process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.process.kill()


@dataclass
class Runner:
    """Run Lean sources, through a kept REPL per workspace when there is one, else one process per source."""

    repls: dict[Path, Repl | None] = field(default_factory=dict)

    def repl(self, root: Path) -> Repl | None:
        """Return the workspace's REPL, starting it on first use, or `None` to run files."""
        if root not in self.repls:
            binary = repl_binary(root)
            process = None
            if binary is not None:
                process = subprocess.Popen(  # noqa: S603  # nosec B603 - fixed arguments, never a shell
                    [lake(), 'env', str(binary)],
                    cwd=root,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                    text=True,
                    bufsize=1,
                )
            self.repls[root] = None if process is None else Repl(root, process)
        return self.repls[root]

    def run(self, root: Path, source: str) -> tuple[int, str, list[Message]]:
        """Run a source in the workspace.

        Args:
            root: The workspace root.
            source: The Lean source.

        Returns:
            The exit status (1 when an error was reported), the error output, and the messages.
        """
        repl = self.repl(root)
        if repl is None:
            return run_file(root, source)
        try:
            messages = repl.run(source)
        except ToolError:
            repl.close()
            self.repls[root] = None
            return run_file(root, source)
        return (1 if any(m.severity == 'error' for m in messages) else 0), '', messages

    def close(self) -> None:
        """Stop every REPL."""
        for repl in self.repls.values():
            if repl is not None:
                repl.close()
