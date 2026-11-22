"""Run the console sessions of a documentation page, in a workspace holding the example study."""

import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXAMPLES = ROOT / 'docs' / 'examples'
STUDY = 'social-science'
PROMPT = '$ '
ELLIPSIS = '…'
TIMEOUT = 600
GIT_IDENTITY = {
    'GIT_AUTHOR_NAME': 'Ada',
    'GIT_AUTHOR_EMAIL': 'ada@example.org',
    'GIT_COMMITTER_NAME': 'Ada',
    'GIT_COMMITTER_EMAIL': 'ada@example.org',
}


@dataclass(frozen=True)
class Command:
    """A command of a console session, with the output the page shows for it.

    Args:
        text: The command, without its prompt, continuation lines joined.
        expected: The output the page shows.
        line: The page's line number of the command.
    """

    text: str
    expected: str
    line: int


def read_commands(page: Path) -> list[Command]:
    """Return the commands of a page's `console` blocks, in page order.

    Args:
        page: The Markdown page.

    Returns:
        The commands, each with the output shown after it.
    """
    commands: list[Command] = []
    lines = page.read_text().splitlines()
    inside = False
    current: list[str] = []
    output: list[str] = []
    start = 0

    def close() -> None:
        """Keep the command being read, if any."""
        if current:
            commands.append(Command(' '.join(current), '\n'.join(output), start))

    for number, line in enumerate(lines, 1):
        if line.strip() == '```console':
            inside, current, output = True, [], []
        elif inside and line.strip() == '```':
            close()
            inside, current, output = False, [], []
        elif inside and line.startswith(PROMPT):
            close()
            current, output, start = [line.removeprefix(PROMPT).removesuffix('\\').strip()], [], number
        elif inside and current and current[-1:] and lines[number - 2].endswith('\\') and not output:
            current.append(line.removesuffix('\\').strip())
        elif inside:
            output.append(line)
    return commands


def matches(expected: str, actual: str) -> bool:
    r"""Return whether an output matches the page's text, where `…` stands for any text.

    Args:
        expected: The page's text.
        actual: The command's output.

    Returns:
        Whether they match, with each run of spaces and tabs read as one space.

    Examples:
        >>> matches('found 0.126513 …', 'found 0.126513 (tolerance 0.0005)')
        True
        >>> matches('agrees', 'differs')
        False
        >>> matches('reproduce   agrees', 'reproduce\tagrees')
        True
    """
    pattern = '.*?'.join(re.escape(part) for part in _strip(expected).split(ELLIPSIS))
    return re.fullmatch(pattern, _strip(actual), re.DOTALL) is not None


def _strip(text: str) -> str:
    """Return text with each run of spaces and tabs as one space, no trailing spaces, and no blank lines at its ends."""
    lines = (re.sub(r'[ \t]+', ' ', line).rstrip() for line in text.strip('\n').splitlines())
    return '\n'.join(lines).strip('\n')


def make_workspace(directory: Path, pack: str = STUDY, *, select: bool = False) -> Path:
    """Copy a pack's example files into a new workspace, the example study's by default.

    Args:
        directory: An empty directory.
        pack: The pack whose examples to copy, if it has any.
        select: Whether to write a `veriphy.yaml` selecting the pack, which the overview pages write themselves.

    Returns:
        The workspace.
    """
    example = EXAMPLES / pack
    if example.is_dir():
        for path in example.iterdir():
            shutil.copy(path, directory / path.name)
    if select:
        (directory / 'veriphy.yaml').write_text(f'version: 1\npacks: [{pack}]\n')
    return directory


def run_command(command: Command, workspace: Path) -> str:
    """Run a command in bash in the workspace, with Veriphy's own `veriphy` first on the path.

    Args:
        command: The command.
        workspace: The workspace.

    Returns:
        Its standard output and error, together.
    """
    path = f'{Path(sys.executable).parent}{os.pathsep}{os.environ.get("PATH", "")}'
    env = {**os.environ, **GIT_IDENTITY, 'PATH': path, 'COLUMNS': '120', 'VERIPHY_GRAPH_SETUP': 'off'}
    bash = shutil.which('bash') or 'bash'
    done = subprocess.run(
        [bash, '-c', command.text],
        cwd=workspace,
        env=env,
        capture_output=True,
        text=True,
        timeout=TIMEOUT,
        check=False,
    )
    return done.stdout + done.stderr
