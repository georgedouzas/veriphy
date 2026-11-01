"""Find, build and run `oo-horn`, the verified checker of Horn certificates from Open Ontologies."""

import json
import os
import shutil
import sys
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from veriphy.core import CheckerError
from veriphy.graph._process import find_tool, run_process

REPOSITORY = 'https://github.com/fabio-rovai/open-ontologies'
PINNED_TAG = 'v2.1.0'
CHECKER_VARIABLE = 'VERIPHY_OO_HORN'
CHECKER_BINARY = Path('lean') / '.lake' / 'build' / 'bin' / 'oo-horn'
BUILD_COMMAND = 'sage -python -m veriphy.graph checker build'
ACCEPTED, REJECTED, UNREADABLE = 0, 1, 2
CHECK_TIMEOUT = 600


def cache_dir(environ: Mapping[str, str] | None = None) -> Path:
    """Return the directory that holds the pinned Open Ontologies release.

    Args:
        environ: The environment, `os.environ` when `None`.

    Returns:
        `$XDG_CACHE_HOME/veriphy/open-ontologies/<tag>`, under `~/.cache` when the variable is unset.

    Examples:
        >>> cache_dir({'XDG_CACHE_HOME': '/tmp/cache'}).as_posix()
        '/tmp/cache/veriphy/open-ontologies/v2.1.0'
    """
    env = os.environ if environ is None else environ
    base = Path(env['XDG_CACHE_HOME']) if env.get('XDG_CACHE_HOME') else Path.home() / '.cache'
    return base / 'veriphy' / 'open-ontologies' / PINNED_TAG


@dataclass(frozen=True)
class CheckerLookup:
    """Where Veriphy looked for `oo-horn`, and what it found.

    Args:
        path: The executable, or `None` when none was found.
        searched: The paths looked at, in order.
    """

    path: Path | None
    searched: tuple[Path, ...]


def find_checker(environ: Mapping[str, str] | None = None) -> CheckerLookup:
    """Find `oo-horn`: the path `VERIPHY_OO_HORN` names, else the cached build.

    An explicit path is never replaced.

    Args:
            environ: The environment, `os.environ` when `None`.

    Returns:
            The lookup.

    Examples:
            >>> find_checker({'VERIPHY_OO_HORN': '/missing/oo-horn'}).path is None
            True
    """
    env = os.environ if environ is None else environ
    explicit = env.get(CHECKER_VARIABLE)
    candidate = Path(explicit) if explicit else cache_dir(env) / CHECKER_BINARY
    found = candidate if candidate.is_file() and os.access(candidate, os.X_OK) else None
    return CheckerLookup(found, (candidate,))


def _run(command: list[str], cwd: Path | None = None) -> str:
    """Run a command and return its output, raising with its output when it fails."""
    code, out, err = run_process(command, cwd)
    if code != 0:
        message = f'{" ".join(command)} failed ({code}):\n{out}{err}'
        raise CheckerError(message)
    return out


def _tool(name: str) -> str:
    """Return the path of a tool the build needs."""
    return find_tool(name, 'building the checker needs git and elan (which provides lake)')


def _install_reasoner(package: Path) -> None:
    """Install the release's `open-ontologies-lite` into the running interpreter."""
    uv = shutil.which('uv')
    if uv is not None:
        _run([uv, 'pip', 'install', '--python', sys.executable, str(package)])
        return
    _run([sys.executable, '-m', 'pip', 'install', str(package)])


@dataclass(frozen=True)
class BuildReport:
    """What `build_checker` fetched, built and installed.

    Args:
        tag: The Open Ontologies release.
        commit: The commit the release points to.
        checker: The built `oo-horn`, or `None` when only the reasoner was installed.
        reasoner: The package directory installed as the reasoner.
    """

    tag: str
    commit: str
    checker: Path | None
    reasoner: Path


def build_checker(*, reasoner_only: bool = False, environ: Mapping[str, str] | None = None) -> BuildReport:
    """Fetch the pinned Open Ontologies release into the cache, build `oo-horn` unless built, and install its reasoner.

    Args:
        reasoner_only: Install the reasoner without building the checker.
        environ: The environment, `os.environ` when `None`.

    Returns:
        The report.
    """
    directory = cache_dir(environ)
    if not (directory / '.git').is_dir():
        directory.parent.mkdir(parents=True, exist_ok=True)
        git = _tool('git')
        _run([git, 'clone', '--quiet', '--depth', '1', '--branch', PINNED_TAG, REPOSITORY, str(directory)])
    commit = _run([_tool('git'), 'rev-parse', 'HEAD'], cwd=directory).strip()
    _install_reasoner(directory / 'python')
    checker = None if reasoner_only else directory / CHECKER_BINARY
    if checker is not None and not checker.is_file():
        _run([_tool('lake'), 'build', 'oo-horn'], cwd=directory / 'lean')
    return BuildReport(PINNED_TAG, commit, checker, directory / 'python')


def check_certificate(directory: Path, checker: Path) -> dict[str, object]:
    """Run `oo-horn check` on a certificate directory and return its report with the status it implies.

    The status is `accepted` (exit 0), `rejected` (exit 1), `unreadable` (exit 2) or `unchecked_error`. The verdict
    and the theorem are the checker's own words, copied from its report.

    Args:
        directory: The certificate directory, with `rules.tsv`, `asserted.tsv` and `horn.tsv`.
        checker: The `oo-horn` executable.

    Returns:
        The checker's JSON report, with `status` and `checker` added.
    """
    files = [str(directory / name) for name in ('rules.tsv', 'asserted.tsv', 'horn.tsv')]
    try:
        code, out, err = run_process([str(checker), 'check', *files], timeout=CHECK_TIMEOUT)
    except CheckerError as exc:
        return {'status': 'unchecked_error', 'checker': str(checker), 'error': str(exc)}
    statuses = {ACCEPTED: 'accepted', REJECTED: 'rejected', UNREADABLE: 'unreadable'}
    try:
        report = json.loads(out.strip().splitlines()[-1]) if out.strip() else {}
    except json.JSONDecodeError:
        report = {'output': out}
    if not isinstance(report, dict):
        report = {'output': out}
    status = statuses.get(code, 'unchecked_error')
    return {**report, 'status': status, 'checker': str(checker), 'stderr': err.strip()}


def builtin_rules(checker: Path) -> str:
    """Return the built-in rule table as the checker prints it.

    Args:
        checker: The `oo-horn` executable.

    Returns:
        The table.
    """
    return _run([str(checker), 'rules'])
