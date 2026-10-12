"""Provide a fixture that checks emitted Lean text parses, by running Lean on it."""

import shutil
import subprocess
import textwrap
from collections.abc import Callable
from pathlib import Path

import pytest

from veriphy.toolkit import Lean

REPO = Path(__file__).resolve().parents[2]


def _wrap(snippet: Lean) -> str:
    """Return a Lean example that parses `snippet` in its category, ignoring elaboration failures."""
    body = textwrap.indent(snippet.text, ' ' * 6).lstrip()
    step = f'({body})' if snippet.kind == 'tactic' else f'(have _ := ({body}))'
    return f'example : True := by\n  first\n  | ({step}; try trivial)\n  | trivial\n'


@pytest.fixture
def lean_parses(tmp_path: Path) -> Callable[[list[Lean]], str]:
    """Return a function that runs Lean on snippets and returns its error output (empty when all parse)."""
    lake = shutil.which('lake')
    if lake is None or not (REPO / '.lake').exists():
        pytest.skip('needs a built Lean workspace (`lake build`)')

    def check(snippets: list[Lean]) -> str:
        """Parse the snippets and return Lean's error lines."""
        source = 'import Mathlib.Tactic\n\n' + '\n'.join(_wrap(s) for s in snippets)
        path = tmp_path / 'Emitted.lean'
        path.write_text(source)
        result = subprocess.run([lake, 'env', 'lean', str(path)], cwd=REPO, capture_output=True, text=True, check=False)
        return '\n'.join(line for line in result.stdout.splitlines() if 'error' in line)

    return check
